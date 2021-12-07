from IceFlix.Iceflix_ice import StreamController, TemporaryUnavailable, Unauthorized
from StreamController import StreamControllerI
import os
import hashlib
import glob
import logging
import IceFlix
import sys
import Ice
Ice.loadSlice("IceFlix.ice")


class StreamProviderI(IceFlix.StreamProvider):

    def __init__(self, current=None):
        root_folder = "resources"
        logging.debug("Sirviendo el directorio: %s", root_folder)
        candidates = glob.glob(os.path.join(root_folder, '*'), recursive=True)
        prefix_len = len(root_folder) + 1
        self._root_ = root_folder
        self._idfiles_ = set()

        try:
            catalog_prx = StreamProviderServer.main_connection.getCatalog()
        except IceFlix.TemporaryUnavailable:
            raise IceFlix.TemporaryUnavailable

        # Completar lista de id
        for filename in candidates:
            archivo = filename[prefix_len:]
            with open(archivo, "rb") as f:
                bytes = f.read()
                id_hash = hashlib.sha256(bytes).hexdigest()
                self._idfiles_.add(id_hash)

            catalog_prx.updateMedia(id, filename, self)
                        

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
                    servant = StreamControllerI(name)
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
            self.check_admin(adminToken)
        except Iceflix.TemporaryUnavailable as e, IceFlix.Unauthorized as e:
                raise e

        with open(fileName, "rb") as f:
            bytes = f.read()
            id_hash = hashlib.sha256(bytes).hexdigest()
            self._idfiles_.add(id_hash)

        try:
            catalog_prx = StreamProviderServer.main_connection.getCatalog()
        except IceFlix.TemporaryUnavailable:
            raise IceFlix.TemporaryUnavailable
        else:
            catalog_prx.updateMedia(id_hash, fileName, self)

    def deleteMedia(self, id: str, adminToken: str, current=None):
        # Código método deleteMedia
        # Throws Unauthorized, WrongMediaID
        try:
            self.check_admin(adminToken)
        except Iceflix.TemporaryUnavailable as e, IceFlix.Unauthorized as e:
                raise e        

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
