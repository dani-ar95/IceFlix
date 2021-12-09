#!/usr/bin/python3

from StreamController import StreamControllerI
import os
import hashlib
import glob
import logging
import sys
import Ice
Ice.loadSlice("./iceflix.ice")
import IceFlix


class StreamProviderI(IceFlix.StreamProvider):

    def __init__(self):
        self._idfiles_ = set()

    def getStream(self, mediaId: str, userToken, current=None):
        ''' Factoría de objetos StreamController '''
        
        try:
            self.check_user(userToken)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized
        else:
            if mediaId not in self._idfiles_:
                raise IceFlix.WrongMediaId
            else:
                print("consiguiendo titulo")
                try:
                    medio_info = self._catalog_prx_.getTile(mediaId)
                except (IceFlix.WrongMediaId, IceFlix.TemporaryUnavailable) as e:
                    raise IceFlix.WrongMediaId
                else:
                    print("se procede a crear el stream")
                    name = medio_info.info.name
                    servant = StreamControllerI(name)
                    servant._authenticator_prx_ = self._authenticator_prx_
                    proxy = current.adapter.addWithUUID(servant)
                    return IceFlix.StreamControllerPrx.checkedCast(proxy)


    def isAvailable(self, mediaId: str, current=None):
        ''' Confirma si existe un medio con ese id'''

        return mediaId in self._idfiles_

    def uploadMedia(self, fileName: str, uploader, adminToken: str, current=None):
        ''' Permite al administador subir un archivo al sistema '''

        try:
            self.check_admin(adminToken)
        except (IceFlix.TemporaryUnavailable, IceFlix.Unauthorized) as e:
                raise IceFlix.Unauthorized

        # Recibir archivo por Uploader
        new_file = bytes
        received = bytes
        while True:
            received = uploader.receive(512)
            if not received: 
                break
            new_file += received #Raise UploadError ¿?

        # Calcular el identificador del archivo nuevo
        id_hash = hashlib.sha256(bytes).hexdigest()
        self._idfiles_.add(id_hash)

        # Escribir el archivo nuevo
        new_file_name = os.path.join("media_resources", fileName)
        with open(new_file_name, "wb") as write_pointer:
            write_pointer.write(new_file)

        try:
            catalog_prx = self.main_connection.getCatalog()
        except IceFlix.TemporaryUnavailable:
            raise IceFlix.TemporaryUnavailable
        else:
            catalog_prx.updateMedia(id_hash, fileName, self._proxy_)
            return id_hash

    def deleteMedia(self, mediaId: str, adminToken: str, current=None):
        ''' Perimitme al administrador borrar archivos '''

        try:
            self.check_admin(adminToken)
        except (IceFlix.TemporaryUnavailable, IceFlix.Unauthorized) as e:
                raise IceFlix.Unauthorized

        if id not in self._idfiles_:
            raise IceFlix.WrongMediaID
        else:
            self._idfiles_.remove(id)
            # Avisar al catalog de que no hay medio?

        # Borrar el archivo        elif userToken is None:
            raise IceFlix.Unauthorized    

    def check_admin(self, admin_token: str):
        ''' Comprueba si un token es Administrador '''

        try:
            user = self._main_prx_.isAdmin(admin_token)
        except IceFlix.Unauthorized as e:
            raise e

    def check_user(self, user_token: str):
        ''' Comprueba que la sesion del usuario es la actual '''

        try:
            is_user = self._authenticator_prx_.isAuthorized(user_token)
        except IceFlix.Unauthorized as e:
            raise e
        else:
            return is_user

class StreamProviderServer(Ice.Application):
    def run(self, argv):
        # sleep(1)
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

        adapter = broker.createObjectAdapterWithEndpoints(
            'StreamProviderAdapter', 'tcp -p 9095')
        stream_provider_proxy = adapter.add(
            servant, broker.stringToIdentity('StreamProvider'))

        #---------------------------------------------------------
        root_folder = "media_resources"
        print(f"Sirviendo el directorio: {root_folder}")
        candidates = glob.glob(os.path.join(root_folder, '*'), recursive=True)
        prefix_len = len(root_folder) + 1
        self._root_ = root_folder

        # stringfield del proxy
        proxy = IceFlix.StreamProviderPrx.checkedCast(stream_provider_proxy)

        # Completar lista de id
        for filename in candidates:
            with open("./"+str(filename), "rb") as f:
                bytes = f.read()
                id_hash = hashlib.sha256(bytes).hexdigest()
                servant._idfiles_.add(id_hash)

            #media_name = os.path.split(filename)
            catalog_prx.updateMedia(id_hash, filename, proxy)

        #---------------------------------------------------------
        adapter.activate()

        servant._proxy_ = stream_provider_proxy

        servant._catalog_prx_ = catalog_prx
        servant._authenticator_prx_ = authenticator_prx
        servant._main_prx_ = main_connection

        main_connection.register(stream_provider_proxy)

        self.shutdownOnInterrupt()
        broker.waitForShutdown()


if __name__ == '__main__':
    #MediaCatalogServer().run(sys.argv)
    sys.exit(StreamProviderServer().main(sys.argv))
