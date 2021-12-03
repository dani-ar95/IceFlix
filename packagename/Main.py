import sys, Ice
import Authenticator
import MediaCatalog
Ice.loadSlice('IceFlix.ice')
import IceFlix


class MainI(IceFlix.Main):

    def __init__(self, admin_token):
        properties = self.communicator().getProperties()
        self.token = properties.getProperty('AdminToken')
    
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
        return adminToken == self.token

class MainServer(Ice.Application):
    def run(self, argv):
        token = argv[1]
        broker = self.communicator()
        servant = MainI(token)
        
        adapter = broker.createObjectAdapter('MainAdapter')
        proxy = adapter.add(servant, broker.stringToIdentity('Main'))
        
        adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        #autenticacion del usuario?
        
        return 0

if __name__ == '__main__':
    sys.exit(MainI().main(sys.argv))