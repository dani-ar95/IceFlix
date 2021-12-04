#!/usr/bin/python3

import sys, Ice

Ice.loadSlice('./iceflix.ice')
import IceFlix


class MainI(IceFlix.Main):

    def getAuthenticator(self, current=None):
        # Código
        # Throws ThemporaryUnavailable
        # Retorna objeto tipo Authenticator
        pass

    def getCatalog(self, current=None):
        # Código
        # Throws TemporaryUnavailable
        # Retorna objeto tipo MediaCatalog
        pass

    def register(self, service, current=None):
        print(f"Me ha hablado {service}!!!!!")

        # Código
        # Throws UnkownService
        pass

    def isAdmin(self, adminToken, current=None):
        # Código
        return adminToken == self.__token__

    def __init__(self, current=None):
        self.__servants__ = dict()
        properties = MainServer.communicator().getProperties()
        self.__token__ = properties.getProperty('AdminToken')

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