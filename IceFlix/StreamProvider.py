from StreamController import StreamControllerI
import os
import hashlib
import glob
import logging
import IceFlix
import sys
import Ice
Ice.loadSlice("./iceflix.ice")


class StreamProviderI(IceFlix.StreamProvider):

    def __init__(self):
        print("hola")

    def getStream(self, mediaId: str, userToken, current=None):
        ''' Factoría de objetos StreamController '''
        
        try:
            self.check_user(userToken)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized

        if id not in StreamProviderServer._idfiles_:
            raise IceFlix.WrongMediaId
        else:

            try:
                medio_info = self._catalog_prx_.getTitle(mediaId)
            except (IceFlix.WrongMediaId, IceFlix.TemporaryUnavailable) as e:
                raise e

            else:
                name = medio_info.info.name
                servant = StreamControllerI(name)
                proxy = current.adapter.addWithUUID(servant)
                return IceFlix.StreamControllerPrx.checkedCast(proxy)


    def isAvailable(self, mediaId: str, current=None):
        ''' Confirma si existe un medio con ese id'''

        return mediaId in StreamProviderServer._idfiles_

    def uploadMedia(self, fileName: str, uploader, adminToken: str, current=None):
        # Código del método uploadMedia
        # Throws Unauthorized, UploadError
        # Retorna String
        try:
            self.check_admin(adminToken)
        except (IceFlix.TemporaryUnavailable, IceFlix.Unauthorized) as e:
                raise IceFlix.Unauthorized

        with open(fileName, "rb") as f:
            bytes = f.read()
            id_hash = hashlib.sha256(bytes).hexdigest()
            StreamProviderServer._idfiles_.add(id_hash)

        try:
            catalog_prx = StreamProviderServer.main_connection.getCatalog()
        except IceFlix.TemporaryUnavailable:
            raise IceFlix.TemporaryUnavailable
        else:
            catalog_prx.updateMedia(id_hash, fileName, self) # Hacer que meta su proxy en self

    def deleteMedia(self, id: str, adminToken: str, current=None):
        # Código método deleteMedia
        # Throws Unauthorized, WrongMediaID
        try:
            self.check_admin(adminToken)
        except (IceFlix.TemporaryUnavailable, IceFlix.Unauthorized) as e:
                raise IceFlix.Unauthorized

        if id not in self._idfiles_:
            raise IceFlix.WrongMediaID
        else:
            self._idfiles_.remove(id)
            # Avisar al catalog de que no hay medio?

    def check_admin(self, admin_token: str):
        ''' Comprueba si un token es Administrador '''

        try:
            auth_prx = StreamProviderServer.main_connection.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            raise IceFlix.TemporaryUnavailable
        else:
            if auth_prx.isAdmin(admin_token):
                return True
            else:
                raise IceFlix.Unauthorized

    def check_user(self, user_token: str):
        ''' Comprueba que la sesion del usuario es la actual '''

        try:
            auth_prx = StreamProviderServer.main_connection.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            raise IceFlix.TemporaryUnavailable
        else:
            try:
                user = auth_prx.isAuthorized(user_token)
            except IceFlix.Unauthorized as e:
                raise e

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
        self._idfiles_ = set()

        # stringfield del proxy
        proxy = IceFlix.StreamProviderPrx.checkedCast(stream_provider_proxy)

        # Completar lista de id
        for filename in candidates:
            with open("./"+str(filename), "rb") as f:
                bytes = f.read()
                id_hash = hashlib.sha256(bytes).hexdigest()
                self._idfiles_.add(id_hash)

            catalog_prx.updateMedia(id_hash, filename, proxy)

        #---------------------------------------------------------
        adapter.activate()

        servant._proxy_ = stream_provider_proxy

        servant._catalog_prx_ = catalog_prx

        main_connection.register(stream_provider_proxy)

        self.shutdownOnInterrupt()
        broker.waitForShutdown()


if __name__ == '__main__':
    #MediaCatalogServer().run(sys.argv)
    sys.exit(StreamProviderServer().main(sys.argv))
