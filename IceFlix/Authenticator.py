#!/usr/bin/python3

import sys, Ice
import json
import secrets
from time import sleep

Ice.loadSlice("iceflix.ice")
import IceFlix

class AuthenticatorI(IceFlix.Authenticator):

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

            
    def check_admin(self, admin_token: str):
        ''' Comprueba si un token es Administrador '''

        try:
            auth_prx = AuthenticatorServer.main_connection.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            raise IceFlix.TemporaryUnavailable
        else: 
            if auth_prx.isAdmin(admin_token):
                return True
            else:
                raise IceFlix.Unauthorized
        
class AuthenticatorServer(Ice.Application):
    def run(self, argv):
        #sleep(1)
        self.shutdownOnInterrupt()
        main_service_proxy = self.communicator().stringToProxy(argv[1])
        main_connection = IceFlix.MainPrx.checkedCast(main_service_proxy)
        if not main_connection:
            raise RuntimeError("Invalid proxy")

        broker = self.communicator()
        servant = AuthenticatorI()
        
        adapter = broker.createObjectAdapterWithEndpoints('AuthenticatorAdapter','tcp -p 9091')
        authenticator_proxy = adapter.add(servant, broker.stringToIdentity('Authenticator'))
        
        adapter.activate()
        main_connection.register(authenticator_proxy)
        
        
        self.shutdownOnInterrupt()
        broker.waitForShutdown()
        
sys.exit(AuthenticatorServer().main(sys.argv))
