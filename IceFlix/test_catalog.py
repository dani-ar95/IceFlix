#!/usr/bin/python3
''''Clase que implementa el cliente de IceFlix para pruebas MediaCatalog '''

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
        # Conexión
        proxy = "MediaCatalogPrincipal -t -e 1.1 @ MediaCatalogAdapter1"
        catalog_prx = self.communicator().stringToProxy(proxy)
        catalog_connection = IceFlix.MediaCatalogPrx.checkedCast(catalog_prx)
        self.adapter = self.communicator().createObjectAdapterWithEndpoints('ClientAdapter', 'tcp')
        self.adapter.activate()
        print(f"Conectado a MediaCatalog en proxy {catalog_connection}")

        # Pruebas:
        # Ejecutar: python3 IceFlix/test_catalog.py --Ice.Config=configs/client.config
        print("Probando")



if __name__ == "__main__":
    sys.exit(Cliente().main(sys.argv))