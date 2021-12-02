import sys, Ice
Ice.loadSlice("IceFlix.ice")
import IceFlix
import logging
import glob
import hashlib
import os

from packagename.Iceflix_ice import StreamController

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
            with open (archivo, "rb") as f: 
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

with Ice.initialize(sys.argv) as communicator:
    adapter = communicator.createObjectAdapterWithEndpoints("StreamProvider", "default -p 10000")
    object = StreamProviderI()
    adapter.add(object, communicator.stringToIdentity("StreamProviderID"))
    adapter.activate()
    communicator.waitForShutdown()