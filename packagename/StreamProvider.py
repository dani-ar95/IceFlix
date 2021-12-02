import sys, Ice
Ice.loadSlice("IceFlix.ice")
import IceFlix

class StreamProviderI(IceFlix.StreamProvider):
    
    def getStream(self, id, userToken, current=None):
        # Código método getStream
        # Throws Unauthorized, WrongMediaID
        # Retorna Objeto tipo StreamController
        pass   

    def isAvailable(self, id, current=None):
        # Código método isAvailable
        # Retorna boolean
        pass

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