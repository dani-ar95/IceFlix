#!/usr/bin/python3
# pylint: disable=invalid-name
"""Modulo Servicio de Autenticación"""

from time import sleep
from os import path
import sys
import json
import secrets
import Ice
import IceStorm
import uuid
from IceFlix.volatile_services import UsersDB
from service_announcement import ServiceAnnouncementsListener, ServiceAnnouncementsSender

auth_id = str(uuid.uuid4())

USERS_PATH = path.join("persistence", path.join(path.dirname(__file__), (auth_id + "_users.json")))
SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")
Ice.loadSlice(SLICE_PATH)
import IceFlix # pylint: disable=wrong-import-position

class AuthenticatorI(IceFlix.Authenticator): # pylint: disable=inherit-non-class
    """Sirviente del servicio de autenticación """

    def __init__(self):
        self._active_users_ = {}
        self._main_prx_ = None
        self.service_id = auth_id


    def get_usersDB(self):
        ''' Devuelve estructura UsersDB '''

        users_passwords = {}
        with open(USERS_PATH, "r", encoding="utf8") as f:
            obj = json.load(f)

        for i in obj["users"]:
            users_passwords.update({i["users"], i["password"]})

        return UsersDB(users_passwords, self._active_users_)


    def refreshAuthorization(self, user: str, passwordHash: str, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Actualiza el token de un usuario registrado '''

        with open(USERS_PATH, "r", encoding="utf8") as f:
            obj = json.load(f)

        for i in obj["users"]:
            if i["user"] == user and i["password"] == passwordHash:
                new_token = secrets.token_urlsafe(40)
                self._active_users_.update({user:new_token})
                return new_token

        raise IceFlix.Unauthorized

    def isAuthorized(self, userToken, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Permite conocer si un token está actualizado en el sistema '''

        return userToken in self._active_users_.values()


    def whois(self, userToken, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Permite conocer el usuario asociado a un token'''

        if self.isAuthorized(userToken):
            if userToken in self._active_users_.values():
                info = self._active_users_.items()
                for user in info:
                    if user[1] == userToken:
                        return user[0]
        else:
            raise IceFlix.Unauthorized

    def addUser(self, user, passwordHash, adminToken, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Perimte al administrador añadir usuarios al sistema '''

        try:
            self.check_admin(adminToken)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized

        self.add_user({user, passwordHash})

    def removeUser(self, user, adminToken, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Permite al administrador elminar usuarios del sistema '''

        try:
            self.check_admin(adminToken)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized

        with open(USERS_PATH, "r", encoding="utf8") as reading_descriptor:
            obj = json.load(reading_descriptor)

        for i in obj["users"]:
            if i["user"] == user:
                obj["users"].remove(i)
                break

        with open(USERS_PATH, 'w', encoding="utf8") as file:
            json.dump(obj, file, indent=2)

        if user in self._active_users_:
            self._active_users_.pop(user)


    def check_admin(self, admin_token: str):
        ''' Comprueba si un token es Administrador '''

        is_admin = self._main_prx_.isAdmin(admin_token)
        if not is_admin:
            raise IceFlix.Unauthorized

        return is_admin


    def add_user(self, user_password):
        ''' Permite añadir usuario a partir de una tupla {usuario, password} '''

        user, password = user_password

        with open(USERS_PATH, "r", encoding="utf8") as f:
            obj = json.load(f)

        obj["users"].append({"user": user, "password": password, "tags": {}})

        with open(USERS_PATH, 'w', encoding="utf8") as file:
            json.dump(obj, file, indent=2)

    def add_token(self, user, token):
        ''' Añade o actualiza un token de usuario '''

        self._active_users_.update({user, token})


    def update_users(self, users_passwords):
        ''' Añade o actualiza usuarios y contraseñas '''

        for user_info in users_passwords.items():
            self.add_user(user_info)


    def share_data_with(self, service):
        """ Envía una estructura usersDB al servicio indicado """

        service.updateDB(self.get_usersDB(), self.service_id)


    def updateDB(
        self, values, service_id, current):  # pylint: disable=invalid-name,unused-argument
        """ Actualiza datos locales a partir de una estructura usersDB """

        print(
            "Receiving remote data base from %s to %s", service_id, self.service_id)

        user_passwords = values.get_users_passwords()
        user_tokens = values.get_users_tokens()

        self.servant._active_users_ = user_tokens # Update user tokens
        self.update_users(user_passwords) # Update users and passwords


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

    def run(self, argv):
        ''' Implementación del servidor de autenticación '''
        sleep(1)
        main_service_proxy = self.communicator().stringToProxy(argv[1])
        #main_connection = IceFlix.MainPrx.checkedCast(main_service_proxy)

        broker = self.communicator()
        self.servant = AuthenticatorI()

        self.adapter = broker.createObjectAdapterWithEndpoints('AuthenticatorAdapter', 'tcp -p 9091')
        authenticator_proxy = adapter.addWithUUID(self.servant)

        self.proxy = authenticator_proxy
        self.adapter.activate()
        self.setup_announcements()

        self.announcer.start_service()

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        self.announcer.stop()

if __name__ == '__main__':
    sys.exit(AuthenticatorServer().main(sys.argv))
