#!/usr/bin/python3
# pylint: disable=invalid-name
"""Modulo Servicio Principal"""

from os import path
import sys
import Ice
import uuid
import IceStorm
from iceevents import IceEvents
from service_announcement import ServiceAnnouncementsListener, ServiceAnnouncementsSender

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")

Ice.loadSlice(SLICE_PATH)
import IceFlix

from constants import ANNOUNCEMENT_TOPIC, ICESTORM_PROXY_PROPERTY


class MainI(IceFlix.Main): # pylint: disable=inherit-non-class
    """Sirviente del servicio principal"""

    def __init__(self):
        self._servants_ = set()
        self.service_id = str(uuid.uuid4())

    def getAuthenticator(self, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Devuelve el proxy a un Servicio de Autenticación válido registrado '''

        for servant in self._servants_:
            try:
                is_auth = servant.ice_isA("::IceFlix::Authenticator")
            except Ice.ConnectionRefusedException:
                self._servants_.remove(servant)
            else:
                if is_auth:
                    return IceFlix.AuthenticatorPrx.checkedCast(servant)

        raise IceFlix.TemporaryUnavailable

    def getCatalog(self, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Devuelve el proxy a un Servicio de Catálogo válido registrado '''

        for servant in self._servants_:
            try:
                is_catalog = servant.ice_isA("::IceFlix::MediaCatalog")
            except Ice.ConnectionRefusedException:
                self._servants_.remove(servant)
            else:
                if is_catalog:
                    return IceFlix.MediaCatalogPrx.checkedCast(servant)

        raise IceFlix.TemporaryUnavailable


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
        service.updateDB(None, self.service_id)

    def updateDB(
        self, values, service_id, current
    ):  # pylint: disable=invalid-name,unused-argument
        """Receives the current main service database from a peer."""
        print(
            "Receiving remote data base from %s to %s", service_id, self.service_id
        )


class MainServer(Ice.Application):
    """Servidor del servicio principal"""

    def __init__(self):
        super().__init__()
        self.servant = MainI()
        self.proxy = None
        self.adapter = None
        self.announcer = None
        self.subscriber = None

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
            self.servant, self.servant.service_id, IceFlix.MainPrx
        )

        subscriber_prx = self.adapter.addWithUUID(self.subscriber)
        topic.subscribeAndGetPublisher({}, subscriber_prx)


    def run(self, argv):
        ''' Implementación del servidor principal '''
        broker = self.communicator()
        servant = MainI()
        properties = broker.getProperties()
        servant._token_ = properties.getProperty("AdminToken")

        self.adapter = broker.createObjectAdapter(self.subscriber)
        self.adapter.add(servant, broker.stringToIdentity("Main"))

        self.adapter.activate()

        self.setup_announcements()
        self.announcer.start_service()

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        self.announcer.stop()

        return 0

if __name__ == "__main__":
    sys.exit(MainServer().main(sys.argv))
