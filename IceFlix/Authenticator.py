#!/usr/bin/python3
# pylint: disable=invalid-name
"""Modulo Servicio de Autenticación"""

from time import sleep
from os import path
import sys
import json
import secrets
import Ice

USERS_PATH = path.join(path.dirname(__file__), "users.json")
SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")
Ice.loadSlice(SLICE_PATH)
import IceFlix # pylint: disable=wrong-import-position

class AuthenticatorI(IceFlix.Authenticator): # pylint: disable=inherit-non-class
    """Sirviente del servicio de autenticación"""

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

        with open(USERS_PATH, "r", encoding="utf8") as f:
            obj = json.load(f)

        obj["users"].append({"user": user, "password": passwordHash, "tags": {}})

        with open(USERS_PATH, 'w', encoding="utf8") as file:
            json.dump(obj, file, indent=2)

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

    def share_data_with(self, service):
        """Share the current database with an incoming service."""
        service.updateDB(None, self.service_id)

    def updateDB(
        self, values, service_id, current
    ):  # pylint: disable=invalid-name,unused-argument
        """Receives the current main service database from a peer."""
        print(
            "Receiving remote data base from %s to %s", service_id, self.service_id
        )

    def __init__(self):
        self._active_users_ = {}
        self._main_prx_ = None


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
        main_connection = IceFlix.MainPrx.checkedCast(main_service_proxy)

        broker = self.communicator()
        servant = AuthenticatorI()

        adapter = broker.createObjectAdapterWithEndpoints('AuthenticatorAdapter', 'tcp -p 9091')
        authenticator_proxy = adapter.add(servant, broker.stringToIdentity('Authenticator'))

        adapter.activate()

        self.setup_announcements()
        self.announcer.start_service()

        main_connection.register(authenticator_proxy)
        servant._main_prx_ = main_connection

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        self.announcer.stop()

if __name__ == '__main__':
    sys.exit(AuthenticatorServer().main(sys.argv))
