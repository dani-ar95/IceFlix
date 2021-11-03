import sys, Ice
import IceFlix

class AuthenticatorI(IceFlix.Authenticator):

    def refreshAuthorization(self, user, passwordHash, current=None):
        # Código
        # Throws Unauthorized
        # Retorna String
        pass

    def isAuthorized(self,userToken, current=None):
        # Código
        # Retorna boolean
        pass

    def whois(self, userToken, current=None):
        # Código
        # Throws Unauthorized
        # Retorna string
        pass

    def addUser(self, user, passwordHash, adminToken, current=None):
        # Código
        # Throws Unauthorized
        pass

    def removeUser(self, user, adminToken, current=None):
        # Código
        # Throws Unauthorized
        pass

if __name__ == "__main__":

   with Ice.initialize(sys.argv) as communicator:
    base = communicator.stringToProxy("MainID:default -p 10000")
    controller = IceFlix.MainPrx.checkedCast(base)
    o = AuthenticatorI()
    if not controller:
        raise RuntimeError("Invalid proxy")

    controller.register(o)

#with Ice.initialize(sys.argv) as communicator:
##    adapter = communicator.createObjectAdapterWithEndpoints("Authenticator", "default -p 10000")
#    object = AuthenticatorI()
#    adapter.add(object, communicator.stringToIdentity("AutheticatorID"))
#    adapter.activate()
#    communicator.waitForShutdown()