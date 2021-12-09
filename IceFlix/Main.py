#!/usr/bin/python3

import sys, Ice
Ice.loadSlice("./iceflix.ice")
import IceFlix

class MainI(IceFlix.Main):
    
    def __init__(self, current=None):
        self._servants_ = set()

    def getAuthenticator(self, current=None):
        print("getAuthenticator")
        for servant in self._servants_:
            try:

                is_auth = servant.ice_isA("::IceFlix::Authenticator")
            except Ice.ConnectionRefusedException:
                pass
            else:
                if servant.ice_isA("::IceFlix::Authenticator"):
                    try:
                        response = servant.ice_ping()
                    except Ice.ConnectionRefusedException:
                        self._servants_.remove(servant)
                    if not response:
                        return IceFlix.AuthenticatorPrx.checkedCast(servant)

        raise IceFlix.TemporaryUnavailable("No authenticator available")

    def getCatalog(self, current=None):
        for servant in self._servants_:
            try:
                is_catalog = servant.ice_isA("::IceFlix::MediaCatalog")
            except Ice.ConnectionRefusedException:
                break
            else:
                if is_catalog:
                    try:
                        response = servant.ice_ping()
                    except Ice.ConnectionRefusedException:
                        self._servants_.remove(servant)
                    if not response:
                        return IceFlix.MediaCatalogPrx.checkedCast(servant)
                
        raise IceFlix.TemporaryUnavailable()

    def register(self, service, current=None):
        print("Bienvenido: " + str(type(service)))
        self._servants_.add(service)
        # Throws UnkownService

    def isAdmin(self, adminToken, current=None):
        return adminToken == self._token_


class MainServer(Ice.Application):
    def run(self, argv):
        if len(argv) > 1:
            token = argv[1]
        broker = self.communicator()
        servant = MainI()
        properties = broker.getProperties()
        servant._token_ = properties.getProperty("AdminToken")
        
        adapter = broker.createObjectAdapter("MainAdapter")
        proxy = adapter.add(servant, broker.stringToIdentity("Main"))
        
        adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        #autenticacion del usuario?
        
        return 0
if __name__ == "__main__":
    sys.exit(MainServer().main(sys.argv))
