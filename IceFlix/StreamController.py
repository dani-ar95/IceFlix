#!/usr/bin/python3
# pylint: disable=invalid-name
''' Clase que se encarga del control del streaming, sus instancias cargan un video
     y retornan la uri del streaming '''

from os import path
import sys
import Ice
import iceflixrtsp # pylint: disable=import-error

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")
Ice.loadSlice(SLICE_PATH)
import IceFlix # pylint: disable=wrong-import-position

class StreamControllerI(IceFlix.StreamController): # pylint: disable=inherit-non-class
    ''' Instancia de StreamController '''

    def __init__(self, file_path, current=None): # pylint: disable=invalid-name,unused-argument
        self._emitter_ = None
        self._filename_ = file_path
        try:
            self._fd_ = open(file_path, "rb") # pylint: disable=bad-option-value
        except FileNotFoundError:
            print("Archivo no encontrado: " + file_path)

    def getSDP(self, userToken, port: int, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Retorna la configuracion del flujo SDP '''

        try:
            self.check_user(userToken)
        except IceFlix.Unauthorized as e:
            raise e
        else:
            self._emitter_ = iceflixrtsp.RTSPEmitter(self._filename_, "127.0.0.1", port)
            self._emitter_.start()
            return self._emitter_.playback_uri

    def stop(self, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Detiene la emision del flujo SDP '''

        self._emitter_.stop()

    def check_user(self, user_token):
        ''' Comprueba que la sesion del usuario está actualizada '''

        is_user = self._authenticator_prx_.isAuthorized(user_token)
        if not is_user:
            raise IceFlix.Unauthorized
        return is_user


class StreamControllerServer(Ice.Application): # pylint: disable=invalid-name
    ''' Servidor del controlador de Streaming '''

    def run(self, args): # pylint: disable=unused-argument
        ''' No hace mucho '''

        broker = self.communicator()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()


if __name__ == '__main__':
    sys.exit(StreamControllerServer().main(sys.argv))
