#!/usr/bin/python3
# pylint: disable=invalid-name
"""Modulo Servicio Principal"""

from os import path
import sys
import random
import uuid
import Ice
from IceStorm import TopicManagerPrx, TopicExists # pylint: disable=no-name-in-module, import-error
from volatile_services import VolatileServices # pylint: disable=no-name-in-module, import-error
from service_announcement import ServiceAnnouncementsListener, ServiceAnnouncementsSender # pylint: disable=no-name-in-module, import-error
from constants import ANNOUNCEMENT_TOPIC # pylint: disable=no-name-in-module, import-error

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")

Ice.loadSlice(SLICE_PATH)
try:
    import IceFlix
except ImportError:
    Ice.loadSlice(path.join(path.dirname(__file__), "iceflix.ice"))
    import IceFlix # pylint: disable=wrong-import-position



class MainI(IceFlix.Main): # pylint: disable=inherit-non-class
    """Sirviente del servicio principal"""

    def __init__(self):
        self._token_ = None
        self._servants_ = set()
        self.service_id = str(uuid.uuid4())
        self.auth_services = []
        self.catalog_services = []
        self.actualizado = False
        self.announcements_listener = None

    @property
    def get_volatile_services(self):
        """ Devuelve un objeto VolatlieServices """

        return VolatileServices(self.auth_services, self.catalog_services)


    def getAuthenticator(self, current=None): # pylint: disable=invalid-name,unused-argument
        """ Devuelve un authenticator activo """

        while self.auth_services:
            try:
                auth_prx = random.choice(list(self.auth_services))
                auth_prx.ice_ping()
                return IceFlix.AuthenticatorPrx.uncheckedCast(auth_prx)

            except Ice.ConnectionRefusedException:
                self.auth_services.remove(auth_prx)

        print(f"\n[MAIN] ID: {self.service_id} No hay servicios de autenticación disponibles")
        raise IceFlix.TemporaryUnavailable

    def addAuthenticator(self, auth_prx, current=None): # pylint: disable=invalid-name,unused-argument
        """ Añade un authenticator activo a su lista """

        self.auth_services.append(auth_prx)


    def getCatalog(self, current=None): # pylint: disable=invalid-name,unused-argument
        """ Devuelve un MediaCatalog activo """

        while self.catalog_services:
            try:
                catalog_prx = random.choice(list(self.catalog_services))
                catalog_prx.ice_ping()
                return IceFlix.MediaCatalogPrx.uncheckedCast(catalog_prx)

            except Ice.ConnectionRefusedException:
                self.catalog_services.remove(catalog_prx)

        print(f"\n[MAIN] ID: {self.service_id} No hay servicios de MediaCatalog disponibles")
        raise IceFlix.TemporaryUnavailable


    def updateDB(self, values, service_id, current=None):  # pylint: disable=invalid-name,unused-argument
        """Receives the current main service database from a peer."""

        print(f"[MAIN] ID: {self.service_id}. Recibido VolatileServices de {service_id}.")

        if service_id == self.service_id:
            return

        if not self.auth_services or not self.catalog_services:
            raise IceFlix.UnknownService

        if not self.actualizado:
            self.auth_services = values.get_authenticators()
            self.catalog_services = values.get_catalogs()
            print(f"[MAIN] ID: {self.service_id}. Se han actualizado los servicios de" +
                  f"autenticación y catálogo")
            self.actualizado = True

    def addCatalog(self, catalog_prx, current=None): # pylint: disable=invalid-name,unused-argument
        """ Añade un MediaCatalog activo a su lista """

        self.catalog_services.append(catalog_prx)


    def register(self, service, current=None): # pylint: disable=unused-argument
        ''' Permite registrarse a determinados servicios '''

        possible_servants = set(["MediaCatalog", "Authenticator", "StreamProvider"])
        if service.ice_getIdentity().name in possible_servants:
            self._servants_.add(service)
        else:
            raise IceFlix.UnknownService

    def isAdmin(self, adminToken, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Verifica que un token es de administración '''

        return adminToken == self._token_ # pylint: disable=invalid-name

    def share_data_with(self, service):
        """Share the current database with an incoming service."""
        service.updateDB(self.get_volatile_services, self.service_id)


class MainServer(Ice.Application):
    """Servidor del servicio principal"""

    def __init__(self):
        super().__init__()
        self.servant = MainI()
        self.proxy = None
        self.adapter = None
        self.announcer = None
        self.subscriber = None
        self.register_subscriber = None

    def setup_announcements(self):
        """Configure the announcements sender and listener."""

        communicator = self.communicator()
        topic_manager = TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager")
        )

        try:
            topic = topic_manager.create(ANNOUNCEMENT_TOPIC)
        except TopicExists:
            topic = topic_manager.retrieve(ANNOUNCEMENT_TOPIC)

        self.announcer = ServiceAnnouncementsSender(
            topic,
            self.servant.service_id,
            self.proxy,
        )

        self.subscriber = ServiceAnnouncementsListener(
            self.servant, self.servant.service_id, IceFlix.MainPrx
        )
        subscriber_prx = self.adapter.addWithUUID(self.subscriber)

        topic.subscribeAndGetPublisher({}, subscriber_prx)


    def run(self, args):
        ''' Implementación del servidor principal '''

        broker = self.communicator()

        properties = broker.getProperties()
        self.servant._token_ = properties.getProperty("AdminToken") #pylint: disable=protected-access

        self.adapter = broker.createObjectAdapterWithEndpoints('MainAdapter', 'tcp')
        self.adapter.add(self.servant, broker.stringToIdentity("Main"))
        servant_proxy = self.adapter.add(self.servant, Ice.stringToIdentity("MainPrincipal"))

        self.proxy = servant_proxy
        self.adapter.activate()

        self.setup_announcements()
        self.servant.announcements_listener = self.subscriber
        self.announcer.start_service()

        print(f"[PROXY MAIN] {self.proxy}")

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        self.announcer.stop()

        return 0


if __name__ == "__main__":
    sys.exit(MainServer().main(sys.argv))
