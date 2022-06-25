#!/usr/bin/python3
# pylint: disable=invalid-name
"""Modulo Servicio de Autenticación"""

import random
import threading
from time import sleep
from os import path
import sys
import uuid
import secrets
from json import JSONDecodeError, load, dump
import Ice
from IceStorm import TopicManagerPrx, TopicExists # pylint: disable=no-name-in-module
try:
    import IceFlix
except ImportError:
    Ice.loadSlice(path.join(path.dirname(__file__), "iceflix.ice"))
    import IceFlix # pylint: disable=wrong-import-position
from users_db import UsersDB
from constants import REVOCATIONS_TOPIC, AUTH_SYNC_TOPIC # pylint: disable=no-name-in-module
from service_announcement import ServiceAnnouncementsListener, ServiceAnnouncementsSender
from user_updates import UserUpdatesSender, UserUpdatesListener
from user_revocations import RevocationsListener, RevocationsSender

AUTH_ID = str(uuid.uuid4())

USERS_PATH = path.join(path.dirname(__file__), "users.json")
LOCAL_DB_PATH = path.join(path.join(path.dirname(__file__),
                                    "persistence"), (AUTH_ID + "_users.json"))
SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")



class AuthenticatorI(IceFlix.Authenticator):  # pylint: disable=inherit-non-class
    """Sirviente del servicio de autenticación """

    def __init__(self):

        self._active_users_ = {}
        self._update_users = None
        self.service_id = AUTH_ID
        self._revocations_sender = None
        self._announcements_listener = None
        self._updated = False

    @property
    def get_usersDB(self):
        ''' Devuelve estructura UsersDB '''

        users_passwords = {}
        with open(LOCAL_DB_PATH, "r", encoding="utf8") as f:
            obj = load(f)

        for i in obj["users"]:
            users_passwords.update({i["user"]: i["password"]})

        return UsersDB(users_passwords, self._active_users_)

    def refreshAuthorization(self, user: str, passwordHash: str, current=None):  # pylint: disable=invalid-name,unused-argument
        ''' Actualiza el token de un usuario registrado '''

        with open(LOCAL_DB_PATH, "r", encoding="utf8") as f:
            obj = load(f)

        for i in obj["users"]:
            if i["user"] == user and i["password"] == passwordHash:
                new_token = secrets.token_urlsafe(40)
                self._active_users_.update({user: new_token})
                self._update_users.newToken(user, new_token)
                revoke_timer = threading.Timer(120.0,
                                               self._revocations_sender.revokeToken, [new_token])
                revoke_timer.start()

                print(f"[AUTH] ID: {self.service_id} Nuevo token generado: {new_token}.")
                return new_token

        raise IceFlix.Unauthorized

    def isAuthorized(self, userToken, current=None):  # pylint: disable=invalid-name,unused-argument
        ''' Permite conocer si un token está actualizado en el sistema '''

        return userToken in self._active_users_.values()

    def whois(self, userToken, current=None):  # pylint: disable=invalid-name,unused-argument
        ''' Permite conocer el usuario asociado a un token'''

        if self.isAuthorized(userToken):
            info = self._active_users_.items()
            for user in info:
                if user[1] == userToken:
                    return user[0]
        else:
            raise IceFlix.Unauthorized

        return None

    def addUser(self, user, passwordHash, adminToken, current=None):  # pylint: disable=invalid-name,unused-argument
        ''' Perimte al administrador añadir usuarios al sistema '''

        try:
            if not self.is_admin(adminToken):
                raise IceFlix.Unauthorized
        except IceFlix.TemporaryUnavailable as exc:
            raise IceFlix.TemporaryUnavailable from exc
        user_password = (user, passwordHash)
        self.add_user(user_password, LOCAL_DB_PATH)
        self.add_user(user_password, USERS_PATH)
        self._update_users.newUser(user, passwordHash, self.service_id)

    def removeUser(self, user, adminToken, current=None):  # pylint: disable=invalid-name,unused-argument
        ''' Permite al administrador elminar usuarios del sistema '''

        try:
            if not self.is_admin(adminToken):
                raise IceFlix.Unauthorized
        except IceFlix.TemporaryUnavailable as exc:
            raise IceFlix.TemporaryUnavailable from exc

        self.remove_user(user, LOCAL_DB_PATH)
        self.remove_user(user, USERS_PATH)
        self._revocations_sender.revokeUser(user)

    def updateDB(
            self, values, service_id, current):  # pylint: disable=invalid-name,unused-argument
        """ Actualiza datos locales a partir de una estructura usersDB """

        if self._updated: # Allow only one update
            print(f"[AUTH] ID: {self.service_id}. Actualización de usuarios ya realizada.")
            return
        self._updated = True

        print(f"[AUTH] ID: {self.service_id}. Recibido UsersDB de {service_id}.")

        if service_id not in self._announcements_listener.known_ids:
            raise IceFlix.UnknownService

        user_passwords = values.userPasswords
        user_tokens = values.usersToken

        self._active_users_ = user_tokens  # Update user tokens
        self.update_users(user_passwords)  # Update users and passwords

    def is_admin(self, admin_token: str):
        ''' Comprueba si un token es Administrador '''

        while self._announcements_listener.mains.values():
            main_prx = random.choice(list(self._announcements_listener.mains.values()))
            if main_prx is not None:
                try:
                    main_prx.ice_ping()
                    return main_prx.isAdmin(admin_token)

                except Ice.ConnectionRefusedException:
                    self._announcements_listener.mains.pop(main_prx) # Puede petar
        raise IceFlix.TemporaryUnavailable


    def add_user(self, user_password, file_path):
        ''' Permite añadir usuario user_password partir de una tupla {usuario, password} '''

        if file_path is None: # Invocación remota
            file_path = LOCAL_DB_PATH

        user, password = user_password

        with open(file_path, "r", encoding="utf8") as f:
            try:
                obj = load(f)
            except JSONDecodeError:  # Primer usuario del sistema -> Construir el formato del json
                obj = {
                    "users": [
                        {
                            "user": user,
                            "password": password
                        }
                    ]
                }
            else:
                current_users = [i["user"] for i in obj["users"]]
                if user not in current_users:
                    obj["users"].append(
                        {"user": user, "password": password})
        print(f"[AUTH] ID: {self.service_id} Añadido usuario: {user}.")

        with open(file_path, 'w', encoding="utf8") as file:
            dump(obj, file, indent=2)

    def add_local_user(self, user_password):
        """ Añade un usuario de forma local """

        self.add_user(user_password, LOCAL_DB_PATH)

    def remove_user(self, user, file_path):
        """ Elimina un usuario del archivo persistente """

        with open(file_path, "r", encoding="utf8") as reading_descriptor:
            obj = load(reading_descriptor)

        for i in obj["users"]:
            if i["user"] == user:
                obj["users"].remove(i)
                print(f"[AUTH] ID: {self.service_id} Usuario eliminado: {user}.")
                break

        with open(file_path, 'w', encoding="utf8") as file:
            dump(obj, file, indent=2)

        if user in self._active_users_:
            self._active_users_.pop(user)

    def remove_local_user(self, user):
        """ Elimina un usuario de forma local """

        self.remove_user(user, LOCAL_DB_PATH)

    def remove_token(self, userToken):
        """ Elimina el token de un usuario """

        try:
            user = self.whois(userToken)
            self._active_users_.pop(user)
            print(f"[AUTH] ID: {self.service_id} Token eliminado: {userToken}.")
        except IceFlix.Unauthorized:
            pass

    def add_token(self, user, token):
        ''' Añade o actualiza un token de usuario '''

        self._active_users_.update({user: token})

    def update_users(self, users_passwords):
        ''' Añade o actualiza usuarios y contraseñas '''

        for user_info in users_passwords.items():
            self.add_user(user_info, LOCAL_DB_PATH)

    def create_db(self):
        """ Crea la bbdd si no existe """

        open(LOCAL_DB_PATH, "x", encoding="utf8")
        with open(USERS_PATH, "r", encoding="utf8") as reading_descriptor:
            obj = load(reading_descriptor)

        for i in obj["users"]:
            self.add_user((i["user"], i["password"]), LOCAL_DB_PATH)

    def share_data_with(self, service):
        """ Envía una estructura usersDB al servicio indicado """

        service.updateDB(self.get_usersDB, self.service_id)

    def set_update_users(self, update_users):
        """ Setea la variable _update_users """

        self._update_users = update_users

    def set_revocations_sender(self, revocations_sender):
        """ Setea la variable _revocations_sender """

        self._revocations_sender = revocations_sender

    def set_announcements_listener(self, announcements_listener):
        """ Setea la variable _announcements_listener """

        self._announcements_listener = announcements_listener


class AuthenticatorServer(Ice.Application): #pylint: disable=too-many-instance-attributes
    """Servidor del servicio principal"""

    def __init__(self):
        super().__init__()
        self.announcer = None
        self.subscriber = None
        self.updates_announcer = None
        self.updates_subscriber = None
        self.revocations_announcer = None
        self.revocations_subscriber = None
        self.servant = None
        self.adapter = None
        self.proxy = None

    def setup_announcements(self):
        """Configure the announcements sender and listener."""

        communicator = self.communicator()
        topic_manager = TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager")
        )

        try:
            topic = topic_manager.create("ServiceAnnouncements")
        except TopicExists:
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
        topic_manager = TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager")
        )

        try:
            topic = topic_manager.create(AUTH_SYNC_TOPIC)
        except TopicExists:
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
        topic_manager = TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager")
        )

        try:
            topic = topic_manager.create(REVOCATIONS_TOPIC)
        except TopicExists:
            topic = topic_manager.retrieve(REVOCATIONS_TOPIC)

        self.revocations_announcer = RevocationsSender(
            topic,
            self.servant.service_id,
            self.proxy,
        )

        self.revocations_subscriber = RevocationsListener(
            self.servant, self.proxy, self.servant.service_id, IceFlix.AuthenticatorPrx
        )

        subscriber_prx = self.adapter.addWithUUID(self.revocations_subscriber)
        topic.subscribeAndGetPublisher({}, subscriber_prx)


    def run(self, args): # pylint: disable=unused-argument
        ''' Implementación del servidor de autenticación '''
        sleep(1)

        broker = self.communicator()
        self.servant = AuthenticatorI()

        self.adapter = broker.createObjectAdapterWithEndpoints(
            'AuthenticatorAdapter', 'tcp')
        self.adapter.add(self.servant, broker.stringToIdentity("Authenticator"))
        authenticator_proxy = self.adapter.add(self.servant,
                                               Ice.stringToIdentity("AuthenticatorPrincipal"))

        self.proxy = authenticator_proxy
        self.servant.create_db()
        self.adapter.activate()

        self.setup_announcements()
        self.setup_user_updates()
        self.setup_revocations()

        self.servant.set_update_users(self.updates_announcer)
        self.servant.set_revocations_sender(self.revocations_announcer)
        self.servant.set_announcements_listener(self.subscriber)

        self.announcer.start_service()

        print(f"[AUTH PROXY] {self.proxy}")

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        self.announcer.stop()


if __name__ == '__main__':
    sys.exit(AuthenticatorServer().main(sys.argv))
