#!/usr/bin/python3

import logging
import IceFlix
import sys
import Ice
Ice.loadSlice("IceFlix.ice")


class StreamControllerI(IceFlix.StreamController):

    def __init__(self, mainProxy):
        root_folder = "resources"
        logging.debug("Sirviendo el directorio: %s", root_folder)

    def getSDP(self, userToken, port: int, current=None):
        print(f"Mensaje: {userToken}, comunicado por puerto: {port}")
        print("Token: tuputamadre")

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
        servant = StreamControllerI()

        adapter = broker.createObjectAdapterWithEndpoints(
            'StreamControllerAdapter', 'tcp -p 9094')
        stream_controller_proxy = adapter.add(
            servant, broker.stringToIdentity('StreamController'))

        adapter.activate()

        main_connection.register(stream_controller_proxy)

        self.shutdownOnInterrupt()
        broker.waitForShutdown()


sys.exit(StreamControllerServer().main(sys.argv))
