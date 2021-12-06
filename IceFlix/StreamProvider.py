from IceFlix.Iceflix_ice import StreamController
import os
import hashlib
import glob
import logging
import IceFlix
import sys
import Ice
Ice.loadSlice("IceFlix.ice")


class StreamProviderI(IceFlix.StreamProvider):

    def __init__(self, mainProxy):
        root_folder = "resources"
        logging.debug("Sirviendo el directorio: %s", root_folder)
        candidates = glob.glob(os.path.join(root_folder, '*'), recursive=True)
        prefix_len = len(root_folder) + 1
        self._root_ = root_folder
        self._idfiles_ = set()

        # Completar lista de id
        for filename in candidates:
            archivo = filename[prefix_len:]
            with open(archivo, "rb") as f:
                bytes = f.read()
                readable_hash = hashlib.sha256(bytes).hexdigest()
                self._idfiles_.add(readable_hash)

        # conectarse al main

    def getStream(self, id: str, userToken, current=None):
        ''' Factoría de objetos StreamController '''
        
        try:
            self.check_admin(userToken)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized

        if id not in self._idfiles_:
            raise IceFlix.WrongMediaID
        else:

            try:
                catalog_prx = StreamProviderServer.main_connection.getCatalog()
            except IceFlix.TemporaryUnavailable:
                raise IceFlix.TemporaryUnavailable
            else:
                try:
                    medio_info = catalog_prx.getTitle(id)
                except IceFlix.WrongMediaId as e, IceFlix.TemporaryUnavailable as e:
                    raise e

                else:
                    name = medio_info.info.name
                    servant = StreamController(name)
                    proxy = current.adapter.addWithUUID(servant)
                    return StreamController.RemoteFilePrx.checkedCast(proxy)


    def isAvailable(self, id: str, current=None):
        ''' Confirma si existe un medio con ese id'''

        return id in self._idfiles_

    def uploadMedia(self, fileName: str, uploader, adminToken: str, current=None):
        # Código del método uploadMedia
        # Throws Unauthorized, UploadError
        # Retorna String
        try:
            catalog_prx = StreamProviderServer.main_connection.getCatalog()
        except IceFlix.TemporaryUnavailable:
            raise IceFlix.TemporaryUnavailable
        else:
            catalog_prx.updateMedia(id, fileName, uploader)

    def deleteMedia(self, id: str, adminToken: str, current=None):
        # Código método deleteMedia
        # Throws Unauthorized, WrongMediaID
        pass

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

class StreamProviderServer(Ice.Application):
    def run(self, argv):
        # sleep(1)
        self.shutdownOnInterrupt()
        main_service_proxy = self.communicator().stringToProxy(argv[1])
        main_connection = IceFlix.MainPrx.checkedCast(main_service_proxy)
        if not main_connection:
            raise RuntimeError("Invalid proxy")

        broker = self.communicator()
        servant = StreamProviderI()

        adapter = broker.createObjectAdapterWithEndpoints(
            'StreamProviderAdapter', 'tcp -p 9095')
        stream_provider_proxy = adapter.add(
            servant, broker.stringToIdentity('StreamProvider'))

        adapter.activate()

        main_connection.register(stream_provider_proxy)

        self.shutdownOnInterrupt()
        broker.waitForShutdown()


sys.exit(StreamProviderServer().main(sys.argv))
