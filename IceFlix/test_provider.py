#!/usr/bin/python3
''''Clase que implementa el cliente de IceFlix para pruebas StreamProvider '''

from os import system, path
from time import sleep
import sys
import Ice
from MediaUploader import MediaUploaderI

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
        # Conexión
        proxy = "ProviderPrincipal -t -e 1.1 @ StreamProviderAdapter1"
        provider_prx = self.communicator().stringToProxy(proxy)
        provider_connection = IceFlix.StreamProviderPrx.checkedCast(provider_prx)
        self.adapter = self.communicator().createObjectAdapterWithEndpoints('ClientAdapter', 'tcp')
        print(f"Conectado a StreamProvider en proxy {provider_connection}")
        self.adapter.activate()

        # Pruebas:
        # Ejecutar: python3 IceFlix/test_provider.py --Ice.Config=configs/client.config
        print("Probando")



if __name__ == "__main__":
    sys.exit(Cliente().main(sys.argv))