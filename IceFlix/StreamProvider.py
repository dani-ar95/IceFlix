#!/usr/bin/python3

from StreamController import StreamControllerI
from os import path, remove
import hashlib
import glob
import logging
import sys
import Ice
from time import sleep


SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")
Ice.loadSlice(SLICE_PATH)
import IceFlix


class StreamProviderI(IceFlix.StreamProvider):

    def __init__(self):
        self._provider_media_ = dict()

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
                    asked_media = self._catalog_prx_.getTile(mediaId) # Pedir medio al catalogo
                except IceFlix.WrongMediaId:
                    raise IceFlix.WrongMediaId
                
            print("consiguiendo titulo")
            if asked_media:
                provide_media = asked_media
            else:
                print("se procede a crear el stream")
                name = provide_media.info.name
                print(provide_media)
                servant = StreamControllerI(name)
                servant._authenticator_prx_ = self._authenticator_prx_
                proxy = current.adapter.addWithUUID(servant)
                return IceFlix.StreamControllerPrx.checkedCast(proxy)


    def isAvailable(self, mediaId: str, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Confirma si existe un medio con ese id'''

        return mediaId in self._provider_media_.keys()

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

        try:
            media_file = self._catalog_prx_.getTile(mediaId)
        except IceFlix.WrongMediaId:
            raise IceFlix.WrongMediaId

        else:
            filename = media_file.info.name
            remove(filename)


    def check_admin(self, admin_token: str):
        ''' Comprueba si un token es Administrador '''

        try:
            user = self._main_prx_.isAdmin(admin_token)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized
        else:
            return user

    def check_user(self, user_token: str):
        ''' Comprueba que la sesion del usuario es la actual '''

        try:
            is_user = self._authenticator_prx_.isAuthorized(user_token)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized
        else:
            return is_user

class StreamProviderServer(Ice.Application):
    ''' Servidor que envía '''
    def run(self, argv):
        '''' Inicialización de la clase '''

        sleep(2)
        self.shutdownOnInterrupt()
        main_service_proxy = self.communicator().stringToProxy(argv[1])
        main_connection = IceFlix.MainPrx.checkedCast(main_service_proxy)
        if not main_connection:
            raise RuntimeError("Invalid proxy")

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
        #---------------------------------------------------------
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
                info = IceFlix.MediaInfo(filename, [])
                new_media = IceFlix.Media(id_hash, proxy, info)
                servant._provider_media_.update({id_hash: new_media})

            #media_name = os.path.split(filename)
            catalog_prx.updateMedia(id_hash, filename, proxy)

        #---------------------------------------------------------
        adapter.activate()

        servant._proxy_ = proxy

        servant._catalog_prx_ = catalog_prx
        servant._authenticator_prx_ = authenticator_prx
        servant._main_prx_ = main_connection

        main_connection.register(stream_provider_proxy)

        self.shutdownOnInterrupt()
        broker.waitForShutdown()


if __name__ == '__main__':
    #MediaCatalogServer().run(sys.argv)
    sys.exit(StreamProviderServer().main(sys.argv))
