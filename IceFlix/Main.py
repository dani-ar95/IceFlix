#!/usr/bin/python3
# pylint: disable=invalid-name
"""Modulo Servicio Principal"""

from os import path
import sys
import Ice
import uuid
import IceStorm
import random
from volatile_services import VolatileServices
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
        self.auth_services = []
        self.catalog_services = []
        self.actualizado = False

    @property
    def get_volatile_services(self):
        return VolatileServices(self.auth_services, self.catalog_services)

    # def getAuthenticator(self, current=None): # pylint: disable=invalid-name,unused-argument
        # ''' Devuelve el proxy a un Servicio de Autenticación válido registrado '''

        # for servant in self._servants_:
            # try:
                # is_auth = servant.ice_isA("::IceFlix::Authenticator")
            # except Ice.ConnectionRefusedException:
                # self._servants_.remove(servant)
            # else:
                # if is_auth:
                    # return IceFlix.AuthenticatorPrx.checkedCast(servant)

        # raise IceFlix.TemporaryUnavailable

    def getAuthenticator(self, current=None):
        while self.auth_services:
            try:
                auth_prx = random.choice(list(self.auth_services))
                auth_prx.ice_ping()
                print('\n[MAIN] Se ha encontrado el proxy de autenticador: ', auth_prx)
                return IceFlix.AuthenticatorPrx.uncheckedCast(auth_prx)
            
            except Ice.ConnectionRefusedException:
                self.auth_services.remove(auth_prx)

        print("\n[MAIN] No hay servicios de autenticación disponibles")
        raise IceFlix.TemporaryUnavailable
    
    def addAuthenticator(self, auth_prx, current=None):
        self.auth_services.append(auth_prx)
        

    # def getCatalog(self, current=None): # pylint: disable=invalid-name,unused-argument
        # ''' Devuelve el proxy a un Servicio de Catálogo válido registrado '''

        # for servant in self._servants_:
            # try:
                # is_catalog = servant.ice_isA("::IceFlix::MediaCatalog")
            # except Ice.ConnectionRefusedException:
                # self._servants_.remove(servant)
            # else:
                # if is_catalog:
                    # return IceFlix.MediaCatalogPrx.checkedCast(servant)

        # raise IceFlix.TemporaryUnavailable

    def getCatalog(self, current=None):
        while self.catalog_services:
            try:
                catalog_prx = random.choice(list(self.catalog_services))
                catalog_prx.ice_ping()
                print('\n[MAIN] Se ha encontrado el proxy de catálogo: ', catalog_prx)
                return IceFlix.MediaCatalogPrx.uncheckedCast(catalog_prx)
            
            except Ice.ConnectionRefusedException:
                self.catalog_services.remove(catalog_prx)

        print("\n[MAIN] No hay servicios de autenticación disponibles")
        raise IceFlix.TemporaryUnavailable
    
    def addCatalog(self, catalog_prx, current=None):
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
        service.updateDB(self.get_volatile_services(), self.service_id)
        

    def updateDB(
        self, values, service_id, current=None
    ):  # pylint: disable=invalid-name,unused-argument
        """Receives the current main service database from a peer."""
        print(
            "Receiving remote data base from %s to %s", service_id, self.service_id
        )
        
        if service_id == self.service_id:
            print("[MAIN] No se puede actualizar la base de datos con la misma instancia")
            return 

        # TODO: COMPROBAR QUE ES TIPO MAIN(?)
        
        if not self.auth_services or not self.catalog_services:
            raise IceFlix.UnknownService
        
        if not self.actualizado:
            self.auth_services = values.get_authenticators()
            self.catalog_services = values.get_catalogs()
            print("[MAIN] Se han actualizado los servicios de autenticación y catálogo")
            self.actualizado = True
        
        

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
            topic = topic_manager.create(ANNOUNCEMENT_TOPIC)
        except IceStorm.TopicExists:
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


    def run(self, argv):
        ''' Implementación del servidor principal '''
        broker = self.communicator()

        self.servant = MainI()

        properties = broker.getProperties()
        self.servant._token_ = properties.getProperty("AdminToken")
        self.adapter = broker.createObjectAdapterWithEndpoints('MainAdapter', 'tcp')
        servant_proxy = self.adapter.addWithUUID(self.servant)

        self.proxy = servant_proxy
        self.adapter.activate()
        self.setup_announcements()
        
        self.announcer.start_service()

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        self.announcer.stop()

        return 0


class RegisterServices(IceFlix.ServiceAnnouncements):
    """Registra los servicios de autenticación y catálogo"""

    def __init__(self, own_servant, own_service_id, own_type):
        self.servant = own_servant
        self.service_id = own_service_id
        self.own_type = own_type

        self.known_ids = set()
        
    def newService(self, service_type, service_id, current=None):
        if service_id == self.service_id or service_id in self.known_ids:
            return
   
        if service_type.ice_isA("::IceFlix::Authenticator"):
            self.servant.auth_services.append(service_id)
            print("[MAIN] Se ha registrado el servicio de autenticación: ", service_id)

        if service_type.ice_isA("::IceFlix::MediaCatalog"):
            self.servant.catalog_services.append(service_id)
            print("[MAIN] Se ha registrado el servicio de catálogo: ", service_id)
    
    def announce(self, service_type, service_id, current = None):
        pass

    
if __name__ == "__main__":
    sys.exit(MainServer().main(sys.argv))
