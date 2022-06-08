""" Modulo para debugear el topic User updates """

from time import sleep
import os
import sys
import json
import secrets
import Ice
import IceStorm
import uuid
from Authenticator import AuthenticatorI

try:
    import IceFlix
except ImportError:
    Ice.loadSlice(os.path.join(os.path.dirname(__file__), "iceflix.ice"))
    import IceFlix


""" Clases para debuguear """

class UserUpdatesListener(IceFlix.UserUpdates):
    """ Listener del topic User updates """

    def __init__(self, own_servant, own_service_id, own_type):
        """ Inicialización del listener """

        self.servant = own_servant
        self.service_id = own_service_id
        self.own_type = own_type

        self.authenticators = {}
        self.catalogs = {}
        self.mains = {}
        self.known_ids = set()

    def newUser(self, user, passwordHash, srvId, current=None):
        """ Comportamiento al recibir un mensaje newUser """

        print(f"[UserUpdates] New User: ID: {srvId}, Usuario: {user}, Contraseña: {passwordHash}")


    def newToken(self, user, userToken, srvId, current=None):
        """ Comportamiento al recibir un mensaje newToken """

        print(f"[UserUpdates] New Token: ID: {srvId}, Usuario: {user}, Token: {userToken}")


class UserUpdatesSender:
    """ Sender del topic User updates """

    def __init__(self, topic, service_id, servant_proxy):
        pass

    def newUser(self, user, passwordHash, srvId, current=None):
        pass


    def newToken(self, user, userToken, srvId, current=None):
        pass


""" Ejecutable """


class DebugAuthenticator(Ice.Application):
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

        self.announcer = UserUpdatesSender(topic, self.servant.service_id,
            self.proxy,
        )

        self.subscriber = UserUpdatesListener(self.servant, self.servant.service_id,
            IceFlix.AuthenticatorPrx
        )

        subscriber_prx = self.adapter.addWithUUID(self.subscriber)
        topic.subscribeAndGetPublisher({}, subscriber_prx)


    def run(self, argv):
        ''' Implementación del debug de UserUpdates '''

        sleep(1)
        main_service_proxy = self.communicator().stringToProxy(argv[1])
        #main_connection = IceFlix.MainPrx.checkedCast(main_service_proxy)

        broker = self.communicator()
        servant = AuthenticatorI()

        adapter = broker.createObjectAdapterWithEndpoints('AuthenticatorAdapter', 'tcp -p 9091')
        authenticator_proxy = adapter.add(servant, broker.stringToIdentity('Authenticator'))

        adapter.activate()

        self.setup_announcements()
        self.announcer.start_service()

        #main_connection.register(authenticator_proxy)
        #servant._main_prx_ = main_connection

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        self.announcer.stop()

if __name__ == '__main__':
    sys.exit(DebugAuthenticator().main(sys.argv))