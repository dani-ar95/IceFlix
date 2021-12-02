import sys, Ice
import json
import secrets

Ice.loadSlice("Iceflix.ice")
import IceFlix

class AuthenticatorI(IceFlix.Authenticator):

    def __init__(self, argv):
        self.shutdownOnInterrupt()
        base = communicator.stringToProxy("MainID:default -p 10000")
        controller = IceFlix.MainPrx.checkedCast(base)
        if not controller:
            raise RuntimeError("Invalid proxy")

        o = AuthenticatorI()
        controller.register(o)

    def refreshAuthorization(self, user, passwordHash, current=None):
        # Código
        obj = json.load(open("users.json"))

        for i in xrange(len(obj)):
            if obj[i]["user"] == user and obj[i]["password"] == passwordHash:
                new_token = secrets.token_urlsafe(40)
                obj[i]["user_token"] = new_token
                return new_token
   
        raise IceFlix.Unauthorized
        # Throws Unauthorized
        # Retorna String
        pass

    def isAuthorized(self,userToken, current=None):
        # Código
        obj = json.load(open("users.json"))

        for i in xrange(len(obj)):
            if obj[i]["user_token"] == userToken:
                return True

        raise IceFlix.Unauthorizedd
        # Retorna boolean

    def whois(self, userToken, current=None):
        # Código
        obj = json.load(open("users.json"))

        for i in xrange(len(obj)):
            if obj[i]["user_token"] == userToken:
                return obj[i]["user"]

        raise IceFlix.Unauthorized      
        # Throws Unauthorized
        # Retorna string

    def addUser(self, user, passwordHash, adminToken, current=None):
        # Comprobar admin
        # Comunica con isAdmin()::Main para comprobar que es admin
            #Si no es admin lanza excepción
            #raise IceFlix.Unauthorized    
        # raise Unauthorized
        # Añadir usuario
        with open ("users.json", "r+") as fp:
            data = json.load(fp)
            data["user"] = user
            data["password"] = passwordHash
            data["user_token"] = secrets.token_urlsafe(40)
            fp.seek(0)
            json.dump(data, fp, indent=4)
            fp.truncate()
            


    def removeUser(self, user, adminToken, current=None):
        # Comprobar admin

        # raise Unautorized
        # Eliminar usuario
        obj = json.load(open("users.json"))

        for i in xrange(len(obj)):
            if obj[i]["user"] == user:
                obj.pop(i)
                break
        # Throws Unauthorized

if __name__ == "__main__":
    with Ice.initialize(sys.argv) as communicator:
        self.shutdownOnInterrupt()
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