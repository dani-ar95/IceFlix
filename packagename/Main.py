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


if __name__ == '__main__':
    sys.exit(MainI().main(sys.argv))
    
with Ice.initialize(sys.argv) as communicator:
    adapter = communicator.createObjectAdapterWithEndpoints("Main", "default -p 10000")
    #object MainI()
    adapter.add(object, communicator.stringToIdentity("MainID"))
    adapter.activate()
    communicator.waitForShutdown()