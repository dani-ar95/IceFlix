#!/usr/bin/python3
# pylint: disable=invalid-name
"""Modulo Servicio de Autenticación"""

    
from cmath import e
import random
from time import sleep
from os import path
import sys
import json
import secrets
import Ice
import IceStorm
import uuid
try:
    import IceFlix
except ImportError:
    Ice.loadSlice(path.join(path.dirname(__file__), "iceflix.ice"))
    import IceFlix # pylint: disable=wrong-import-position
from volatile_services import UsersDB
from service_announcement import ServiceAnnouncementsListener, ServiceAnnouncementsSender
from user_updates import UserUpdatesSender, UserUpdatesListener
from user_revocations import RevocationsListener, RevocationsSender
from constants import ANNOUNCEMENT_TOPIC, REVOCATIONS_TOPIC, AUTH_SYNC_TOPIC

auth_id = str(uuid.uuid4())

USERS_PATH = "./users.json"
LOCAL_DB_PATH = path.join(path.join(path.dirname(__file__),
                       "persistence"), (auth_id + "_users.json"))
SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")
Ice.loadSlice(SLICE_PATH)


class AuthenticatorI(IceFlix.Authenticator):  # pylint: disable=inherit-non-class
    """Sirviente del servicio de autenticación """

    def __init__(self):
        self._active_users_ = {}
        self._update_users = None
        self.service_id = auth_id
        self._revocations_sender = None
        self._announcements_listener = None

    @property
    def get_usersDB(self):
        ''' Devuelve estructura UsersDB '''

        users_passwords = {}
        with open(LOCAL_DB_PATH, "r", encoding="utf8") as f:
            obj = json.load(f)

        for i in obj["users"]:
            users_passwords.update({i["user"]: i["password"]})

        return UsersDB(users_passwords, self._active_users_)

    def refreshAuthorization(self, user: str, passwordHash: str, current=None):  # pylint: disable=invalid-name,unused-argument
        ''' Actualiza el token de un usuario registrado '''

        with open(LOCAL_DB_PATH, "r", encoding="utf8") as f:
            obj = json.load(f)
        
        for i in obj["users"]:
            if i["user"] == user and i["password"] == passwordHash:
                new_token = secrets.token_urlsafe(40)
                self._active_users_.update({user: new_token})
                return new_token

        raise IceFlix.Unauthorized

    def isAuthorized(self, userToken, current=None):  # pylint: disable=invalid-name,unused-argument
        ''' Permite conocer si un token está actualizado en el sistema '''

        return userToken in self._active_users_.values()

    def whois(self, userToken, current=None):  # pylint: disable=invalid-name,unused-argument
        ''' Permite conocer el usuario asociado a un token'''

        if self.isAuthorized(userToken):
            if userToken in self._active_users_.values():
                info = self._active_users_.items()
                for user in info:
                    if user[1] == userToken:
                        return user[0]
        else:
            raise IceFlix.Unauthorized

    def addUser(self, user, passwordHash, adminToken, current=None):  # pylint: disable=invalid-name,unused-argument
        ''' Perimte al administrador añadir usuarios al sistema '''

        try:
            self.check_admin(adminToken)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized

        a = (user, passwordHash)
        self.add_user(a, LOCAL_DB_PATH)
        self._update_users.newUser(
            user, passwordHash, self.service_id)  # No testeado

    def removeUser(self, user, adminToken, current=None):  # pylint: disable=invalid-name,unused-argument
        ''' Permite al administrador elminar usuarios del sistema '''

        try:
            self.check_admin(adminToken)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized

        self.remove_user(user, LOCAL_DB_PATH)
        self._revocations_sender.revokeUser(user, self.service_id)

    def check_admin(self, admin_token: str):
        ''' Comprueba si un token es Administrador '''
        main_prx = random.choice(list(self._announcements_listener.mains.values()))
        is_admin = main_prx.isAdmin(admin_token)
        if not is_admin:
            raise IceFlix.Unauthorized

        return is_admin

    def add_user(self, user_password, path):
        ''' Permite añadir usuario a partir de una tupla {usuario, password} '''

        user, password = user_password

        print(user_password)

        with open(path, "r", encoding="utf8") as f:
            try:
                obj = json.load(f)
            except Exception as e:  # Primer usuario del sistema -> Construir el formato del json
                obj = {
                    "users": [
                        {
                            "user": user,
                            "password": password,
                            "tags": {}
                        }
                    ]
                }
            else:
                current_users = [i["user"] for i in obj["users"]]
                if (user not in current_users):
                    obj["users"].append(
                        {"user": user, "password": password, "tags": {}})

        with open(path, 'w', encoding="utf8") as file:
            json.dump(obj, file, indent=2)

    def remove_user(self, user, path):
        """ Elimina un usuario del archivo persistente """

        with open(path, "r", encoding="utf8") as reading_descriptor:
            obj = json.load(reading_descriptor)

        for i in obj["users"]:
            if i["user"] == user:
                obj["users"].remove(i)
                break

        with open(path, 'w', encoding="utf8") as file:
            json.dump(obj, file, indent=2)

        if user in self._active_users_:
            self._active_users_.pop(user)

    def remove_token(self, userToken):
        """ Elimina el token de un usuario """

        usuarios = self._active_users_.items()

        for tuple in usuarios:
            if userToken in tuple:
                self._active_users_.pop(tuple)

    def add_token(self, user, token):
        ''' Añade o actualiza un token de usuario '''

        self._active_users_.update({user, token})

    def update_users(self, users_passwords):
        ''' Añade o actualiza usuarios y contraseñas '''

        for user_info in users_passwords.items():
            self.add_user(user_info, LOCAL_DB_PATH)

    def create_db(self):
        open(LOCAL_DB_PATH, "x")
        with open(USERS_PATH, "r", encoding="utf8") as reading_descriptor:
            obj = json.load(reading_descriptor)

        for i in obj["users"]:
            self.add_user(
                (i["user"], i["password"]), LOCAL_DB_PATH)

    def share_data_with(self, service):
        """ Envía una estructura usersDB al servicio indicado """

        service.updateDB(self.get_usersDB, self.service_id)

    def updateDB(
            self, values, service_id, current):  # pylint: disable=invalid-name,unused-argument
        """ Actualiza datos locales a partir de una estructura usersDB """

        print(f"Receiving remote data base from {service_id} to {self.service_id}")

        user_passwords = values.userPasswords
        user_tokens = values.usersToken

        self._active_users_ = user_tokens  # Update user tokens
        self.update_users(user_passwords)  # Update users and passwords


class AuthenticatorServer(Ice.Application):
    """Servidor del servicio principal"""

    def setup_announcements(self):
        """Configure the announcements sender and listener."""

        communicator = self.communicator()
        topic_manager = IceStorm.TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager")
        )

        try:
            topic = topic_manager.create("ServiceAnnouncements")
        except IceStorm.TopicExists:
            topic = topic_manager.retrieve("ServiceAnnouncements")

        self.announcer = ServiceAnnouncementsSender(
            topic,
            self.servant.service_id,
            self.proxy,
        )

        self.subscriber = ServiceAnnouncementsListener(
            self.servant, self.servant.service_id, IceFlix.AuthenticatorPrx
        )

        subscriber_prx = self.adapter.addWithUUID(self.subscriber)
        topic.subscribeAndGetPublisher({}, subscriber_prx)

    def setup_user_updates(self):
        """ Configurar sender y listener del topic User Updates """

        communicator = self.communicator()
        topic_manager = IceStorm.TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager")
        )

        try:
            topic = topic_manager.create(AUTH_SYNC_TOPIC)
        except IceStorm.TopicExists:
            topic = topic_manager.retrieve(AUTH_SYNC_TOPIC)

        self.updates_announcer = UserUpdatesSender(
            topic,
            self.servant.service_id,
            self.proxy,
        )

        self.updates_subscriber = UserUpdatesListener(
            self.servant, self.servant.service_id, IceFlix.AuthenticatorPrx
        )

        subscriber_prx = self.adapter.addWithUUID(self.updates_subscriber)
        topic.subscribeAndGetPublisher({}, subscriber_prx)


    def setup_revocations(self):
        """ Configurar sender y listener del topic Revocations """

        communicator = self.communicator()
        topic_manager = IceStorm.TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager")
        )

        try:
            topic = topic_manager.create(REVOCATIONS_TOPIC)
        except IceStorm.TopicExists:
            topic = topic_manager.retrieve(REVOCATIONS_TOPIC)

        self.revocations_announcer = RevocationsSender(
            topic,
            self.servant.service_id,
            self.proxy,
        )

        self.revocations_subscriber = RevocationsListener(
            self.servant, self.servant.service_id, IceFlix.AuthenticatorPrx
        )

        subscriber_prx = self.adapter.addWithUUID(self.revocations_subscriber)
        topic.subscribeAndGetPublisher({}, subscriber_prx)


    def run(self, argv):
        ''' Implementación del servidor de autenticación '''
        sleep(1)

        broker = self.communicator()
        self.servant = AuthenticatorI()

        self.adapter = broker.createObjectAdapterWithEndpoints(
            'AuthenticatorAdapter', 'tcp')
        authenticator_proxy = self.adapter.addWithUUID(self.servant)

        self.proxy = authenticator_proxy
        self.servant.create_db()
        self.adapter.activate()

        self.setup_announcements()
        self.setup_user_updates()
        self.setup_revocations()

        self.servant._update_users = self.updates_announcer
        self.servant._revocations_sender = self.revocations_announcer
        self.servant._announcements_listener = self.subscriber

        self.announcer.start_service()

        #print(f"[AUTH PROXY] {self.proxy}")

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        self.announcer.stop()


if __name__ == '__main__':
    sys.exit(AuthenticatorServer().main(sys.argv))
