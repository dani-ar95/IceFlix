#!/usr/bin/python3
# pylint: disable=invalid-name
''' Servicio de Streaming '''

from os import path, remove
import hashlib
import glob
import sys
from time import sleep
import Ice

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")

Ice.loadSlice(SLICE_PATH)
import IceFlix

from StreamController import StreamControllerI # pylint: disable=import-error

class StreamProviderI(IceFlix.StreamProvider): # pylint: disable=inherit-non-class
    ''' Instancia de Stream Provider '''

    def __init__(self):
        self._provider_media_ = {}

        self._proxy_ = None
        self._catalog_prx_ = None
        self._authenticator_prx_ = None
        self._main_prx_ = None

    def getStream(self, mediaId: str, userToken: str, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Factoría de objetos StreamController '''

        try:
            self.check_user(userToken)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized
        else:
            asked_media = None
            if self.isAvailable(mediaId):
                provide_media = self._provider_media_.get(mediaId)
            else:
                try:
                    asked_media = self._catalog_prx_.getTile(mediaId)
                except IceFlix.WrongMediaId:
                    raise IceFlix.WrongMediaId

            if asked_media:
                provide_media = asked_media
            else:
                name = provide_media.info.name
                print(provide_media)
                servant = StreamControllerI(name)
                servant._authenticator_prx_ = self._authenticator_prx_
                proxy = current.adapter.addWithUUID(servant)
                return IceFlix.StreamControllerPrx.checkedCast(proxy)


    def isAvailable(self, mediaId: str, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Confirma si existe un medio con ese id'''

        return mediaId in self._provider_media_

    def uploadMedia(self, fileName: str, uploader, adminToken: str, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Permite al administador subir un archivo al sistema '''

        try:
            self.check_admin(adminToken)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized
        else:
            new_file = b""
            received = b""

            try:
                while True:
                    received = uploader.receive(512)
                    if not received:
                        break
                    new_file += received
            except:
                raise IceFlix.UploadError

            id_hash = hashlib.sha256(new_file).hexdigest()

            file = path.split(fileName)[1]
            new_file_name = path.join(path.dirname(__file__), "media_resources/" + file)

            with open(new_file_name, "wb") as write_pointer:
                write_pointer.write(new_file)

            # Crear el media propio
            info = IceFlix.MediaInfo(new_file_name, [])
            new_media = IceFlix.Media(id_hash, self._proxy_, info)
            self._provider_media_.update({id_hash:new_media})

            # Enviar medio al catálogo
            self._catalog_prx_.updateMedia(id_hash, fileName, self._proxy_)

            return id_hash

    def deleteMedia(self, mediaId: str, adminToken: str, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Perimite al administrador borrar archivos conociendo su id '''

        try:
            self.check_admin(adminToken)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized

        if mediaId in self._provider_media_:
            filename = self._provider_media_.get(mediaId).info.name
        else:
            try:
                media_file = self._catalog_prx_.getTile(mediaId)
            except IceFlix.WrongMediaId:
                raise IceFlix.WrongMediaId
            else:
                filename = media_file.info.name
        remove(filename)

    def check_admin(self, admin_token: str):
        ''' Comprueba si un token es Administrador '''

        is_admin = self._main_prx_.isAdmin(admin_token)
        if not is_admin:
            raise IceFlix.Unauthorized
        return is_admin

    def check_user(self, user_token: str):
        ''' Comprueba que la sesion del usuario es la actual '''

        is_user = self._authenticator_prx_.isAuthorized(user_token)
        if not is_user:
            raise IceFlix.Unauthorized
        else:
            return is_user

class StreamProviderServer(Ice.Application):
    ''' Servidor que envía '''

    def run(self, argv):
        '''' Inicialización de la clase '''

        sleep(3)
        main_service_proxy = self.communicator().stringToProxy(argv[1])
        main_connection = IceFlix.MainPrx.checkedCast(main_service_proxy)

        broker = self.communicator()
        try:
            catalog_prx = main_connection.getCatalog()
        except IceFlix.TemporaryUnavailable:
            raise IceFlix.TemporaryUnavailable

        try:
            authenticator_prx = main_connection.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            raise IceFlix.TemporaryUnavailable

        servant = StreamProviderI()

        adapter = broker.createObjectAdapterWithEndpoints('StreamProviderAdapter', 'tcp -p 9095')
        stream_provider_proxy = adapter.add(servant, broker.stringToIdentity('StreamProvider'))

        root_folder = path.join(path.dirname(__file__), "media_resources")
        print(f"Sirviendo el directorio: {root_folder}")
        candidates = glob.glob(path.join(root_folder, '*'), recursive=True)

        # stringfield del proxy
        proxy = IceFlix.StreamProviderPrx.checkedCast(stream_provider_proxy)

        # Completar lista de id
        for filename in candidates:
            with open("./"+str(filename), "rb") as f:
                print("Sirviendo " + str(filename))
                bytes = f.read()
                id_hash = hashlib.sha256(bytes).hexdigest()
                new_media = IceFlix.Media(id_hash, proxy, IceFlix.MediaInfo(filename, []))
                servant._provider_media_.update({id_hash: new_media})

            catalog_prx.updateMedia(id_hash, filename, proxy)

        adapter.activate()

        servant._proxy_ = proxy

        servant._catalog_prx_ = catalog_prx
        servant._authenticator_prx_ = authenticator_prx
        servant._main_prx_ = main_connection

        main_connection.register(stream_provider_proxy)

        self.shutdownOnInterrupt()
        broker.waitForShutdown()


if __name__ == '__main__':
    sys.exit(StreamProviderServer().main(sys.argv))
