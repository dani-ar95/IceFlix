#!/usr/bin/python3

import sys, Ice

Ice.loadSlice('./iceflix.ice')
import IceFlix


class MainI(IceFlix.Main):
    
    def __init__(self, current=None):
        self._servants_ = dict()
        properties = MainServer.communicator().getProperties()
        self._token_ = properties.getProperty('AdminToken')

    def getAuthenticator(self, current=None):
        # Código
        auth = self._servants_.get("<class 'IcePy.ObjectPrx'>", None)
        if auth:
            return auth
        else: 
            raise IceFlix.TemporaryUnavailable
        # Throws ThemporaryUnavailable
        # Retorna objeto tipo Authenticator
        pass

    def getCatalog(self, current=None):
        catalog = self._servants_.get("<class 'IcePy.ObjectPrx'>", None)
        if catalog:
            return catalog
        else: 
            raise IceFlix.TemporaryUnavailable
        # Throws TemporaryUnavailable
        # Retorna objeto tipo MediaCatalog
        pass

    def register(self, service, current=None):
        print(f"Me ha hablado {service}!!!!!")
        self._servants_.update({type(service): service})
        # Throws UnkownService
        pass

    def isAdmin(self, adminToken, current=None):
        # Código
        return adminToken == self._token_


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