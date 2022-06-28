#!/usr/bin/python3
''''Clase que implementa el cliente de IceFlix para pruebas StreamProvider '''

import hashlib
import secrets
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
        provider_connection = IceFlix.StreamProviderPrx.uncheckedCast(provider_prx)
        self.adapter = self.communicator().createObjectAdapterWithEndpoints('ClientAdapter', 'tcp')
        print(f"Conectado a StreamProvider en proxy {provider_connection}")
        self.adapter.activate()

        # Pruebas:
        # Ejecutar: python3 IceFlix/test_provider.py --Ice.Config=configs/client.config
        print("Probando")

        auth_proxy = "AuthenticatorPrincipal -t -e 1.1 @ AuthenticatorAdapter1"
        auth_prx = self.communicator().stringToProxy(auth_proxy)
        auth_connection = IceFlix.AuthenticatorPrx.uncheckedCast(auth_prx)

        user2 = "user"
        pass2 = "password"
        hash = hashlib.sha256(pass2.encode()).hexdigest()
        token_valido = auth_connection.refreshAuthorization(user2, hash)
        print(token_valido)
        token_incorrecto = secrets.token_urlsafe(40)

        mediaid_valido = "0be6efeb267ef1dc271a9a740ee2a82bfe0527ac22ba18b7aa419cfb961aea1e"
        wrong_mediaId = "a"

        nombre_valido = "IceFlix/local/maincra.mp4"
        nombre_incorrecto = "aaaaaa"

        admin_token = "admin"

        # uploader = MediaUploaderI(nombre_valido)

        # adapter = self.communicator().createObjectAdapterWithEndpoints(
        #     'MediaUploaderAdapter', 'tcp')
        # uploader_proxy = adapter.addWithUUID(uploader)
        # uploader_connection = IceFlix.MediaUploaderPrx.uncheckedCast(uploader_proxy)

        # GET_STREAM ##################################################################################
        # print("\nPRUEBA GET_STREAM MEDIA_ID VALIDO Y TOKEN VALIDO")
        # try:
        #     print("getStream()=", provider_connection.getStream(mediaid_valido, token_valido), " EXITO")
        # except IceFlix.Unauthorized as e:
        #     print(e, " FAIL")
        # except IceFlix.WrongMediaId as e:
        #     print(e, " FAIL")
        
        # print("\nPRUEBA GET_STREAM TOKEN INCORRECTO")
        # try:
        #     print("getStream()=", provider_connection.getStream(mediaid_valido, token_incorrecto), " FAIL")
        # except IceFlix.Unauthorized as e:
        #     print(e, " EXITO")
        # except IceFlix.WrongMediaId as e:
        #     print(e, " FAIL")

        # print("\nPRUEBA GET_STREAM MEDIA_ID INCORRECTO")
        # try:
        #     print("getStream()=", provider_connection.getStream(wrong_mediaId, token_valido), " FAIL")
        # except IceFlix.Unauthorized as e:
        #     print(e, " FAIL")
        # except IceFlix.WrongMediaId as e:
        #     print(e, " EXITO")

        # # IS_AVAILABLE ##################################################################################
        # print("\nPRUEBA IS_AVAILABLE MEDIA_ID CORRECTO")
        # is_available = provider_connection.isAvailable(mediaid_valido)
        # print(is_available)
        # if is_available == True:
        #     print("EXITO")
        # else:
        #     print("FAIL")
        
        # print("\nPRUEBA IS_AVAILABLE MEDIA_ID INCORRECTO")
        # is_available = provider_connection.isAvailable(wrong_mediaId)
        # print(is_available)
        # if is_available == False:
        #     print("EXITO")
        # else:
        #     print("FAIL")

        # UPLOAD_MEDIA #############################################################################
        # print("\nPRUEBA UPLOAD_MEDIA NOMBRE CORRECTO Y ES ADMIN")
        # try:
        #     print("uploadMedia()=", provider_connection.uploadMedia(nombre_valido, uploader_connection, admin_token), " EXITO")
        # except IceFlix.UploadError as e:
        #     print(e, " FAIL")
        # except IceFlix.Unauthorized as e:
        #     print(e, " FAIL")

        # print("\nPRUEBA UPLOAD_MEDIA NOMBRE INCORRECTO")
        # try:
        #     print("uploadMedia()=", provider_connection.uploadMedia(nombre_incorrecto, uploader_connection, admin_token), " FAIL")
        # except IceFlix.UploadError as e:
        #     print(e, " EXITO")
        # except IceFlix.Unauthorized as e:
        #     print(e, " FAIL")

        # print("\nPRUEBA UPLOAD_MEDIA NO ES ADMIN")
        # try:
        #     print("uploadMedia()=", provider_connection.uploadMedia(nombre_valido, uploader_connection, "uu"), " FAIL")
        # except IceFlix.UploadError as e:
        #     print(e, " FAIL")
        # except IceFlix.Unauthorized as e:
        #     print(e, " EXITO")

        # DELETE_MEDIA ######################################################################################
        print("\nPRUEBA DELETE_MEDIA MEDIA_ID CORRECTO Y ES ADMIN")
        try:
            print("deleteMedia()=", provider_connection.deleteMedia(mediaid_valido, admin_token), " EXITO")
        except IceFlix.WrongMediaId as e:
            print(e, " FAIL")
        except IceFlix.Unauthorized as e:
            print(e, " FAIL")

        print("\nPRUEBA DELETE_MEDIA MEDIA_ID INCORRECTO")
        try:
            print("deleteMedia()=", provider_connection.deleteMedia(wrong_mediaId, admin_token), " FAIL")
        except IceFlix.WrongMediaId as e:
            print(e, " EXITO")
        except IceFlix.Unauthorized as e:
            print(e, " FAIL")

        print("\nPRUEBA DELETE_MEDIA NO ES ADMIN")
        try:
            print("deleteMedia()=", provider_connection.deleteMedia(mediaid_valido, "uu"), " FAIL")
        except IceFlix.WrongMediaId as e:
            print(e, " FAIL")
        except IceFlix.Unauthorized as e:
            print(e, " EXITO")

if __name__ == "__main__":
    sys.exit(Cliente().main(sys.argv))