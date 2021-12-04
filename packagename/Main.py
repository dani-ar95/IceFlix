#!/usr/bin/python3

import sys, Ice

Ice.loadSlice('./iceflix.ice')
import IceFlix

class MainI(IceFlix.Main):

    def getAuthenticator(self, current=None):
        # Código
        auth_prx = self._servants_.get("Authenticator", None)
        if auth_prx:
            return auth_prx
        else: 
            raise IceFlix.TemporaryUnavailable
        # Throws ThemporaryUnavailable
        # Retorna objeto tipo Authenticator

    def getCatalog(self, current=None):
        catalog_prx = self._servants_.get("MediaCatalog", None)
        if catalog_prx:
            return catalog_prx
        else: 
            raise IceFlix.TemporaryUnavailable
        # Throws TemporaryUnavailable
        # Retorna objeto tipo MediaCatalog

    def register(self, service, current=None):
        permitidos = set("MediaUploader", "Authenticator", "MediaCatalog", "StreamController", "StreamProvider")

        identidad = service.ice_getIdentity()
        nombre_servicio = MainServer.communicator().identityToString(identidad)

        if nombre_servicio in permitidos:
            self._servants_.update({nombre_servicio: service})
        else:
            raise IceFlix.UnkownService

    def isAdmin(self, adminToken, current=None):
        return adminToken == self._token_

    def __init__(self, current=None):
        self._servants_ = dict()
        properties = MainServer.communicator().getProperties()
        self._token_ = properties.getProperty('AdminToken')

class MainServer(Ice.Application):
    def run(self, argv):
        token = argv[1]
        broker = self.communicator()
        servant = MainI()
        
        adapter = broker.createObjectAdapter('MainAdapter')
        proxy = adapter.add(servant, broker.stringToIdentity('Main'))
        
        adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        #autenticacion del usuario?
        
        return 0

sys.exit(MainServer().main(sys.argv))