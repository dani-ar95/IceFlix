#!/usr/bin/python3

import sys, Ice
from os import path

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")
Ice.loadSlice(SLICE_PATH)
import IceFlix


class MediaUploaderI(IceFlix.MediaUploader):

    def __init__(self, file_name):
        try:
            self.__fd__ = open(file_name, "rb") # pylint: disable=consider-using-with
        except FileNotFoundError:
            print("Archivo no encontrado: " + str(file_name))

    def receive(self, size: int, current=None): # pylint: disable=unused-argument
        chunk = self.__fd__.read(size)
        return chunk

    def close(self, current=None): # pylint: disable=unused-argument
        self.__fd__.close()


class MediaUploaderServer(Ice.Application):
    def run(self, argv):
        #sleep(1)
        self.shutdownOnInterrupt()
        main_service_proxy = self.communicator().stringToProxy(argv[1])
        main_connection = IceFlix.MainPrx.checkedCast(main_service_proxy)
        if not main_connection:
            raise RuntimeError("Invalid proxy")

        broker = self.communicator()
        '''servant = MediaUploaderI()
        
        adapter = broker.createObjectAdapterWithEndpoints('MediaUploaderAdapter','tcp -p 9093')
        authenticator_proxy = adapter.add(servant, broker.stringToIdentity('MediaUploader'))
        
        adapter.activate()
        
        main_connection.register(authenticator_proxy)'''
        
        self.shutdownOnInterrupt()
        broker.waitForShutdown()
        
if __name__ == "__main__":
    sys.exit(MediaUploaderServer().main(sys.argv))
