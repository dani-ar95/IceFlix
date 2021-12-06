#!/usr/bin/python3

from logging import exception
import sys, Ice
import json
import secrets
from time import sleep

Ice.loadSlice("iceflix.ice")
import IceFlix

class AuthenticatorI(IceFlix.Authenticator):

    def refreshAuthorization(self, user, passwordHash, current=None):
        ''' Genera un nuevo token para el usuario y contraseña dados'''

        obj = json.load(open("users.json"))

        for i in xrange(len(obj)):
            if obj[i]["user"] == user and obj[i]["password"] == passwordHash:
                new_token = secrets.token_urlsafe(40)
                obj[i]["user_token"] = new_token
                return new_token
   
        raise IceFlix.Unauthorized

    def isAuthorized(self,userToken, current=None):
        ''' Comprueba si el token de usuario está registrado '''

        obj = json.load(open("users.json"))

        for i in xrange(len(obj)):
            if obj[i]["user_token"] == userToken:
                return True

        raise IceFlix.Unauthorizedd

    def whois(self, userToken, current=None):
        ''' Devuelve el nombre del usuario con el token dado '''

        obj = json.load(open("users.json"))

        for i in xrange(len(obj)):
            if obj[i]["user_token"] == userToken:
                return obj[i]["user"]

        raise IceFlix.Unauthorized

    def addUser(self, user, passwordHash, adminToken, current=None):
        ''' Permite al Administrador añadir un usuario '''

        if check_admin(adminToken):
            with open ("users.json", "r+") as fp:
                data = json.load(fp)
                data["user"] = user
                data["password"] = passwordHash
                data["user_token"] = secrets.token_urlsafe(40)
                fp.seek(0)
                json.dump(data, fp, indent=4)
                fp.truncate()


    def removeUser(self, user, adminToken, current=None):
        ''' Permite al Administrador eliminar un usuario '''

        if check_admin(adminToken):
        # raise Unautorized
        # Eliminar usuario
            obj = json.load(open("users.json"))

            for i in xrange(len(obj)):
                if obj[i]["user"] == user:
                    obj.pop(i)
                    break
        # Throws Unauthorized

            
    def check_admin(admin_token: str):
        ''' Comprueba si un token es Administrador '''

        try:
            auth_prx = AuthenticatorServer.getAuthenticator()
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
        print(type(authenticator_proxy))
        main_connection.register(authenticator_proxy)
        
        self.shutdownOnInterrupt()
        broker.waitForShutdown()
        
sys.exit(AuthenticatorServer().main(sys.argv))
