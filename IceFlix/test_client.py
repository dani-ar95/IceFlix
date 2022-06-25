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
        print("Prueba isAuthorized(Manoloooo)")
        print(auth_connection.isAuthorized("Manolooooo"))

if __name__ == "__main__":
    sys.exit(Cliente().main(sys.argv))
