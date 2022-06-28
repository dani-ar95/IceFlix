#!/usr/bin/python3
''''Clase que implementa el cliente de IceFlix para pruebas Authenticator '''

from os import system, path
from time import sleep
import sys
import signal
import hashlib
import getpass
import Ice
import iceflixrtsp
from MediaUploader import MediaUploaderI
import IceStorm
import secrets
from user_revocations import RevocationsListener, RevocationsSender
from constants import REVOCATIONS_TOPIC  #pylint: disable=no-name-in-module

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")
Ice.loadSlice(SLICE_PATH)
import IceFlix # pylint: disable=wrong-import-position

class Cliente(Ice.Application): #pylint: disable=too-many-instance-attributes,too-many-public-methods
    ''' Implementación del cliente '''

    def __init__(self):
        super().__init__()

    def run(self, args):
        # Hacer cosas
        proxy = "AuthenticatorPrincipal -t -e 1.1 @ AuthenticatorAdapter1"
        auth_prx = self.communicator().stringToProxy(proxy)
        auth_connection = IceFlix.AuthenticatorPrx.checkedCast(auth_prx)
        self.adapter = self.communicator().createObjectAdapterWithEndpoints('ClientAdapter', 'tcp')
        self.adapter.activate()
        print(f"Conectado a authenticator en proxy {auth_prx}")
        
        # Conexión hecha, se pueden probar las cosas
        token = secrets.token_urlsafe(40)
        print("PRUEBAS TOKEN NO VALIDO, expected False y UNAUTHORIZED")
        print("isAuthorized()=", auth_connection.isAuthorized(token))
        try:
            print("whois()=", auth_connection.whois(token), ", FAIL")
        except IceFlix.Unauthorized as e:
            print("whois()=", e, ", EXITO")
        
        print("\nPRUEBA USUARIO NO EXISTE, expected UNAUTHORIZED")
        user = "sergios"
        password = "password"
        hash = hashlib.sha256(password.encode()).hexdigest()
        try:
            print("refreshAuthorization()= ", auth_connection.refreshAuthorization(user, hash), ", FAIL")
        except IceFlix.Unauthorized as e:
            print("refreshAuthorization()= ", e, ", EXITO")
            
        print("\nPRUEBA REFRESHAUTH USUARIO EXISTE, expected TOKEN")
        user2 = "user"
        pass2 = "password"
        hash = hashlib.sha256(pass2.encode()).hexdigest()
        try:
            token_valido = auth_connection.refreshAuthorization(user2, hash)
            print("refreshAuthorization()= ", token_valido, "EXITO")
        except IceFlix.Unauthorized as e:
            print("refreshAuthorization()= ", e, ", FAIL")
        
        print("\nPRUEBA AÑADIR/BORRAR USUARIOS SIN TOKEN ADMIN, expected UNAUTHORIZED or TEMPUNAVAILABLE ")
        admin_token = "token"
        try:
            print("addUser()=", auth_connection.addUser(user, hash, admin_token), "FAIL")
        except IceFlix.Unauthorized as e:
            print("addUser()=", e, ", EXITO")
        except IceFlix.TemporaryUnavailable as e:
            print("addUser()=", e, ", FAIL")
            
        try:
            print("removeUser()=", auth_connection.removeUser(user, admin_token), "FAIL")
        except IceFlix.Unauthorized as e:
            print("removeUser()=", e, ", EXITO")
        except IceFlix.TemporaryUnavailable as e:
            print("removeUser()=", e, ", FAIL")
        
        print("\nPRUEBA CON TOKEN VALIDO, expected TRUE y USUARIO")
        print("isAuthorized()=", auth_connection.isAuthorized(token_valido))
        try:
            print("whois()=", auth_connection.whois(token_valido), ", EXITO")
        except IceFlix.Unauthorized as e:
            print("whois()=", e, ", FRACASO")
            
        print("\nPRUEBA AÑADIR/BORRAR USUARIOS CON TOKEN ADMIN, expected None (EXITO) ")
        admin_token = "admin"
        try:
            print("addUser()=", auth_connection.addUser(user, hash, admin_token), "EXITO")
        except IceFlix.Unauthorized as e:
            print("addUser()=", e, ", FAIL")
        except IceFlix.TemporaryUnavailable as e:
            print("addUser()=", e, ", FAIL")

        try:
            print("removeUser()=", auth_connection.removeUser(user, admin_token), "EXITO")
        except IceFlix.Unauthorized as e:
            print("removeUser()=", e, ", FAIL")
        except IceFlix.TemporaryUnavailable as e:
            print("removeUser()=", e, ", FAIL")

        print("\nPRUEBA AÑADIR/BORRAR USUARIOS MAIN NO DISPONIBLE")
        try:
            print("addUser()=", auth_connection.addUser(user, hash, admin_token), "FAIL")
        except IceFlix.TemporaryUnavailable as e:
            print("addUser=", e, "EXITO")

        try:
            print("removeUser()=", auth_connection.removeUser(user, admin_token), "FAIL")
        except IceFlix.TemporaryUnavailable as e:
            print("removeUser()=", e, ", EXITO")
            

if __name__ == "__main__":
    sys.exit(Cliente().main(sys.argv))
