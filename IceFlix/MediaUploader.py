#!/usr/bin/python3

import sys, Ice
Ice.loadSlice("./iceflix.ice")
import IceFlix


class MediaUploaderI(IceFlix.MediaUploader):

    def __init__(self, file_name):
        try:
            self.__fd__ = open(file_name, "rb")
        except FileNotFoundError:
            print("Archivo no encontrado: " + str(file_name))

    def receive(self, size: int, current=None):
        chunk = self._fd_.read(size)
        return chunk

    def close(self, current=None):
        # Código método Close
        pass


class MediaUploaderServer(Ice.Application):
    def run(self, argv):
        #sleep(1)
        self.shutdownOnInterrupt()
        main_service_proxy = self.communicator().stringToProxy(argv[1])
        main_connection = IceFlix.MainPrx.checkedCast(main_service_proxy)
        if not main_connection:
            raise RuntimeError("Invalid proxy")

        broker = self.communicator()
        servant = MediaUploaderI()
        
        adapter = broker.createObjectAdapterWithEndpoints('MediaUploaderAdapter','tcp -p 9093')
        authenticator_proxy = adapter.add(servant, broker.stringToIdentity('MediaUploader'))
        
        adapter.activate()
        
        main_connection.register(authenticator_proxy)
        
        self.shutdownOnInterrupt()
        broker.waitForShutdown()
        

sys.exit(MediaUploaderServer().main(sys.argv))
