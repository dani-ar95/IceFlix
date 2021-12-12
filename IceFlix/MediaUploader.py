#!/usr/bin/python3

import sys
from os import path
import Ice

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")
Ice.loadSlice(SLICE_PATH)
import IceFlix


class MediaUploaderI(IceFlix.MediaUploader):

    def __init__(self, file_name):
        try:
            self._fd_ = open(file_name, "rb") # pylint: disable=bad-option-value
        except FileNotFoundError:
            self._fd_ = None
            print("Archivo no encontrado: " + str(file_name))

    def receive(self, size: int, current=None): # pylint: disable=unused-argument
        if self._fd_:
            chunk = self._fd_.read(size)
            return chunk

    def close(self, current=None): # pylint: disable=unused-argument
        if self._fd_:
            self._fd_.close()


class MediaUploaderServer(Ice.Application):
    def run(self, argv):
        #sleep(1)
        self.shutdownOnInterrupt()
        main_service_proxy = self.communicator().stringToProxy(argv[1])
        main_connection = IceFlix.MainPrx.checkedCast(main_service_proxy)
        if not main_connection:
            raise RuntimeError("Invalid proxy")

        broker = self.communicator()
        
        self.shutdownOnInterrupt()
        broker.waitForShutdown()
        
if __name__ == "__main__":
    sys.exit(MediaUploaderServer().main(sys.argv))
