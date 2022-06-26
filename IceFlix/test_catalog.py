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
        print(f"Conectado a MediaCatalog en proxy {catalog_connection}")
        self.adapter.activate()

        auth_proxy = "AuthenticatorPrincipal -t -e 1.1 @ AuthenticatorAdapter1"
        auth_prx = self.communicator().stringToProxy(auth_proxy)
        auth_connection = IceFlix.AuthenticatorPrx.uncheckedCast(auth_prx)

        user2 = "user"
        pass2 = "password"
        hash = hashlib.sha256(pass2.encode()).hexdigest()
        token_valido = auth_connection.refreshAuthorization(user2, hash)
        print(token_valido)

        # Pruebas:
        # Ejecutar: python3 IceFlix/test_catalog.py --Ice.Config=configs/client.config
        print("Probando")

        mediaid_valido = "0be6efeb267ef1dc271a9a740ee2a82bfe0527ac22ba18b7aa419cfb961aea1e"
        wrong_mediaId = "a"
        token_incorrecto = secrets.token_urlsafe(40)
        admin_token = "admin"

        # ADD_TAGS ##################################################################################
        # print("\nPRUEBA ADD_TAGS MEDIA_ID VALIDO Y TOKEN VALIDO")
        # try:
        #     print("addTags()=", catalog_connection.addTags(mediaid_valido, ["melon", "sandia"], token_valido), " EXITO")
        # except IceFlix.Unauthorized:
        #     print("Unauthorized FAIL")
        # except IceFlix.WrongMediaId:
        #     print("WrongMediaID FAIL")
        
        # print("\nPRUEBA ADD_TAGS TOKEN NO VÁLIDO")
        # try:
        #     print("addTags()=", catalog_connection.addTags(mediaid_valido, ["melon", "sandia"], token_incorrecto), " FAIL")
        # except IceFlix.Unauthorized as e:
        #     print(e, " EXITO")
        # except IceFlix.WrongMediaId:
        #     print("WrongMediaID FAIL")

        # print("\nPRUEBA ADD_TAGS MEDIA_ID NO VALIDO")
        # try:
        #     print("addTags()=", catalog_connection.addTags(wrong_mediaId, ["melon", "sandia"], token_valido), " FAIL")
        # except IceFlix.WrongMediaId as e:
        #     print(e, " EXITO")
        # except IceFlix.Unauthorized:
        #     print("Unauthorized FAIL")


        # GET_TILE ##################################################################################
        print("\nPRUEBA GET_TILE TOKEN VALIDO Y MEDIAID CORRECTO")
        try:
            print("getTile()=", catalog_connection.getTile(token_valido, mediaid_valido), " EXITO")
        except IceFlix.Unauthorized:
            print("Unauthorized FAIL")
        except IceFlix.WrongMediaId:
            print("WrongMediaID FAIL")

        print("\nPRUEBA GET_TILE TOKEN NO VÁLIDO")
        try:
            print("getTile()=", catalog_connection.getTile(token_incorrecto, mediaid_valido), " FAIL")
        except IceFlix.Unauthorized as e:
            print(e, " EXITO")
        except IceFlix.WrongMediaId:
            print("WrongMediaID FAIL")

        print("\nPRUEBA GET_TILE MEDIA_ID NO VALIDO")
        try:
            print("getTile()=", catalog_connection.getTile(token_valido, wrong_mediaId), " FAIL")
        except IceFlix.WrongMediaId as e:
            print(e, " EXITO")
        except IceFlix.Unauthorized:
            print("Unauthorized FAIL")

        # GET_TILES_BY_NAME ##########################################################################
        print("\nPRUEBA GET_TILES_BY_NAME NOMBRE CORRECTO")
        names = catalog_connection.getTilesByName("Pelucas", True)
        print(names)
        if names != []:
            print("EXITO")
        else:
            print("FAIL")

        print("\nPRUEBA GET_TILES_BY_NAME NOMBRE INCORRECTO")
        names = catalog_connection.getTilesByName("ERPelucas", True)
        print(names)
        if names == []:
            print("EXITO")
        else:
            print("FAIL")

        # GET_TILES_BY_TAGS ###########################################################################
        tags = ["melon", "sandia"]
        tags_incorrectas = ["hola"]

        print("\nPRUEBA GET_TILES_BY_TAGS TOKEN VALIDO Y TAGS CORRECTAS")
        try:
            tags_tiles = catalog_connection.getTilesByTags(tags, False, token_valido)
            print(tags_tiles)
            if tags_tiles != []:
                print("EXITO")
            else:
                print("FAIL")
        except IceFlix.Unauthorized as e:
            print(e, " FAIL")

        print("\nPRUEBA GET_TILES_BY_TAGS TOKEN VALIDO Y TAGS INCORRECTAS")
        try:
            tags_tiles = catalog_connection.getTilesByTags(tags_incorrectas, False, token_valido)
            print(tags_tiles)
            if tags_tiles == []:
                print("EXITO")
            else:
                print("FAIL")
        except IceFlix.Unauthorized as e:
            print(e, " FAIL")

        print("\nPRUEBA GET_TILES_BY_TAGS TOKEN INCORRECTO")
        try:
            tags_tiles = catalog_connection.getTilesByTags(tags, False, token_incorrecto)
            print(tags_tiles)
            if tags_tiles == []:
                print("FAIL")
            else:
                print("FAIL")
        except IceFlix.Unauthorized as e:
            print(e, " EXITO")

        # REMOVE_TAGS ##################################################################################
        print("\nPRUEBA REMOVE_TAGS MEDIA_ID VALIDO Y TOKEN VALIDO")
        try:
            print("removeTags()=", catalog_connection.removeTags(mediaid_valido, ["prueba", "prueba2"], token_valido), " EXITO")
        except IceFlix.Unauthorized:
            print("Unauthorized FAIL")
        except IceFlix.WrongMediaId:
            print("WrongMediaID FAIL")
        
        print("\nPRUEBA REMOVE_TAGS TOKEN NO VÁLIDO")
        try:
            print("removeTags()=", catalog_connection.removeTags(mediaid_valido, ["melon", "sandia"], token_incorrecto), " FAIL")
        except IceFlix.Unauthorized as e:
            print(e, " EXITO")
        except IceFlix.WrongMediaId:
            print("WrongMediaID FAIL")

        print("\nPRUEBA REMOVE_TAGS MEDIA_ID NO VALIDO")
        try:
            print("removeTags()=", catalog_connection.removeTags(wrong_mediaId, ["melon", "sandia"], token_valido), " FAIL")
        except IceFlix.WrongMediaId as e:
            print(e, " EXITO")
        except IceFlix.Unauthorized:
            print("Unauthorized FAIL")

        # RENAME_TILE #########################################################################################
        print("\nPRUEBA RENAME_TILE MEDIA_ID VALIDO Y ADMIN TOKEN VALIDO")
        try:
            print("renameTile()=", catalog_connection.renameTile(mediaid_valido, "Prueba4", admin_token), " EXITO")
        except IceFlix.Unauthorized:
            print("Unauthorized FAIL")
        except IceFlix.WrongMediaId:
            print("WrongMediaID FAIL")
        
        print("\nPRUEBA RENAME_TILE ADMIN TOKEN NO VÁLIDO")
        try:
            print("renameTile()=", catalog_connection.renameTile(mediaid_valido, "Prueba2", "a"), " FAIL")
        except IceFlix.Unauthorized as e:
            print(e, " EXITO")
        except IceFlix.WrongMediaId:
            print("WrongMediaID FAIL")

        print("\nPRUEBA RENAME_TILE MEDIA_ID NO VALIDO")
        try:
            print("renameTile()=", catalog_connection.renameTile(wrong_mediaId, "Prueba3", admin_token), " FAIL")
        except IceFlix.WrongMediaId as e:
            print(e, " EXITO")
        except IceFlix.Unauthorized:
            print("Unauthorized FAIL")

        



if __name__ == "__main__":
    sys.exit(Cliente().main(sys.argv))