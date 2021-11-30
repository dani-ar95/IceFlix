import sys, Ice
import IceFlix
import Authenticator
import MediaCatalog

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
        # Retorna boolean
        pass


with Ice.initialize(sys.argv) as communicator:
    adapter = communicator.createObjectAdapterWithEndpoints("Main", "default -p 10000")
    #object MainI()
    adapter.add(object, communicator.stringToIdentity("MainID"))
    adapter.activate()
    communicator.waitForShutdown()