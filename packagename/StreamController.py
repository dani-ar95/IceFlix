import sys, Ice
import IceFlix
import logging

class StreamControllerI(IceFlix.StreamController):


    def __init__(self, mainProxy):
        root_folder = "resources"
        logging.debug("Sirviendo el directorio: %s", root_folder)

    def getSDP(self, userToken, port: int, current=None):
        print(f"Mensaje: {userToken}, comunicado por puerto: {port}")
        print("Token: tuputamadre")

    def stop(self):
        pass

with Ice.initialize(sys.argv) as communicator:
    adapter = communicator.createObjectAdapterWithEndpoints("StreamControllerAdapter", "default -p 10000")
    object = StreamControllerI()
    adapter.add(object, communicator.stringToIdentity("StreamControllerID"))
    adapter.activate()
    communicator.waitForShutdown()
