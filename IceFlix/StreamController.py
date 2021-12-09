#!/usr/bin/python3

from os import path
import IceFlix
import sys

import Ice

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")
Ice.loadSlice(SLICE_PATH)


class StreamControllerI(IceFlix.StreamController):

    def __init__(self, file_path, current=None):
        self._filename_ = file_path
        try:
            self._fd_ = open(file_path, "rb")
        except FileNotFoundError:
            print("Archivo no encontrado: " + file_path)

    def getSDP(self, userToken, port: int, current=None):
        ''' Retorna la configuracion del flujo SDP '''

        try:
            authenticated = self.check_user(userToken)
        except IceFlix.Unauthorized as e:
            raise e
        else:    
            path = self._filename_
            return str(path) + "::127.0.0.1::" + str(port)

    def stop(self):
        pass

    def check_user(self, user_token):
        ''' Comprueba que la sesion del usuario es la actual '''

        try:
            is_user = self._authenticator_prx_.isAuthorized(user_token)
        except IceFlix.Unauthorized as e:
            raise e
        return is_user


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
