from packagename.Iceflix_ice import StreamController
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

    def getStream(self, id, userToken, current=None):
        # Comprobar autorizacion -> raise IceFlix.Unauthorized
        # Código método getStream
        if id not in self._idfiles_:
            raise IceFlix.WrongMediaID

        servant = StreamController(id)
        proxy = current.adapter.addWithUUID(servant)
        return StreamController.RemoteFilePrx.checkedCast(proxy)
        # Retorna Objeto tipo StreamController

    def isAvailable(self, id, current=None):
        # Código método isAvailable
        return id in self._idfiles_
        # Retorna boolean

    def uploadMedia(self, fileName, uploader, adminToken, current=None):
        # Código del método uploadMedia
        # Throws Unauthorized, UploadError
        # Retorna String
        pass

    def deleteMedia(self, id, adminToken, current=None):
        # Código método deleteMedia
        # Throws Unauthorized, WrongMediaID
        pass


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
