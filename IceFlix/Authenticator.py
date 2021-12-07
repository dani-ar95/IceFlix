#!/usr/bin/python3

import sys, Ice
import json
import secrets
from time import sleep

Ice.loadSlice("iceflix.ice")
import IceFlix

class AuthenticatorI(IceFlix.Authenticator):

    def refreshAuthorization(self, user, passwordHash, current=None):
        ''' Actualiza el token de un usuario registrado '''

        with open("users.json", "r") as f:
            obj = json.load(f)

        for i in obj["users"]:
            if i["user"] == user and i["password"] == passwordHash:
                print("Usuario autenticado")
                new_token = secrets.token_urlsafe(40)
                i["user_token"] = new_token

                with open('users.json', 'w') as file:
                    json.dump(obj, file, indent=2)

                #new = {"user": {"user": i["user"], "password": i["password"], "user_token": new_token}}
                return new_token

        raise IceFlix.Unauthorized

    def isAuthorized(self, userToken, current=None):
        ''' Permite conocer si un token está actualizado en el sistema '''

        with open("users.json", "r") as f:
            obj = json.load(f)

        for i in obj["users"]:
            if i["user_token"] == userToken:
                return True

        raise IceFlix.Unauthorized

    def whois(self, userToken, current=None):
        ''' Permite conocer el usuario asociado a un token'''

        with open("users.json", "r") as f:
            obj = json.load(f)

        for i in obj["users"]:
            if i["user_token"] == userToken:
                return i["user"]

        raise IceFlix.Unauthorized


    def addUser(self, user, passwordHash, adminToken, current=None):
        ''' Perimte al administrador añadir usuarios al sistema '''
        
        try:
            self.check_admin(adminToken)
        except (IceFlix.TemporaryUnavailable, IceFlix.Unauthorized) as e:
            raise IceFlix.Unauthorized

        with open("users.json", "r") as f:
            obj = json.load(f)

        obj["users"].append({"user": user, "password": passwordHash, "user_token": "blank"})

        with open('users.json', 'w') as file:
            json.dump(obj, file, indent=2)

        #new = {"user": {"user": i["user"], "password": i["password"], "user_token": new_token}}
  
            

    def removeUser(self, user, adminToken, current=None):
        ''' Permite al administrador elminar usuarios del sistema '''

        try:
            self.check_admin(adminToken)
        except (IceFlix.TemporaryUnavailable, IceFlix.Unauthorized) as e:
            raise IceFlix.Unauthorized

        with open("users.json", "r") as f:
            obj = json.load(f)

        for i in obj["users"]:
            if i["user"] == user:
                obj.pop(i)
                break

            
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
        broker
        
        self.shutdownOnInterrupt()
        broker.waitForShutdown()
        
if __name__ == '__main__':
    sys.exit(AuthenticatorServer().main(sys.argv))       