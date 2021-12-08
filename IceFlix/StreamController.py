#!/usr/bin/python3

import logging
import IceFlix
import sys
import Ice
import socket
from pathlib import Path

Ice.loadSlice("./iceflix.ice")


class StreamControllerI(IceFlix.StreamController):

    def __init__(self, file_path, current=None):
        self._filename_ = file_path
        try:
            self._fd_ = open(file_path, "rb")
        except FileNotFoundError:
            print("Archivo no encontrado: " + file_path)

    def getSDP(self, userToken, port: int, current=None):
        # Comprobar user autenticado

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("localhost", port))
        file_size = Path(self._filename_).stat().st_size
        sent = 0

        while (sent < file_size):
            s.send(self._fd_.read(512))
            sent + 512

    def stop(self):
        pass


class StreamControllerServer(Ice.Application):
    def run(self, argv):
        # sleep(1)
        self.shutdownOnInterrupt()
        main_service_proxy = self.communicator().stringToProxy(argv[1])
        main_connection = IceFlix.MainPrx.checkedCast(main_service_proxy)
        if not main_connection:
            raise RuntimeError("Invalid proxy")

        broker = self.communicator()
        servant = StreamControllerI("default")

        adapter = broker.createObjectAdapterWithEndpoints(
            'StreamControllerAdapter', 'tcp -p 9094')
        stream_controller_proxy = adapter.add(
            servant, broker.stringToIdentity('StreamController'))

        adapter.activate()

        main_connection.register(stream_controller_proxy)

        self.shutdownOnInterrupt()
        broker.waitForShutdown()


if __name__ == '__main__':
    sys.exit(StreamControllerServer().main(sys.argv))
