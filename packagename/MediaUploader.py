import sys, Ice
Ice.loadSlice("IceFlix.ice")
import IceFlix


class MediaUploaderI(IceFlix.MediaUploader):

    def receive(self, size: int, current=None):
        # Código método Receive
        # Retorna String
        pass   

    def close(self, current=None):
        # Código método Close
        pass
    def destroy(self, current=None):
        # Código método Destroy
        pass

with Ice.initialize(sys.argv) as communicator:
    adapter = communicator.createObjectAdapterWithEndpoints("MediaUploader", "default -p 10000")
    object = MediaUploaderI()
    adapter.add(object, communicator.stringToIdentity("MediaUploaderID"))
    adapter.activate()
    communicator.waitForShutdown()