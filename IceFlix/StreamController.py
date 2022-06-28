#!/usr/bin/python3
# pylint: disable=invalid-name
''' Clase que se encarga del control del streaming, sus instancias cargan un video
     y retornan la uri del streaming '''

from os import path
import random
import uuid
import Ice
import iceflixrtsp # pylint: disable=import-error

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")
Ice.loadSlice(SLICE_PATH)
import IceFlix # pylint: disable=wrong-import-position

class StreamControllerI(IceFlix.StreamController): # pylint: disable=inherit-non-class,too-many-instance-attributes
    ''' Instancia de StreamController '''

    def __init__(self, announcements_listener, filename, userToken, current=None): # pylint: disable=invalid-name,unused-argument
        self._emitter_ = None
        self._filename_ = filename
        self.service_id = str(uuid.uuid4)
        self.announcements_listener = announcements_listener
        self.authentication_timer = None
        self.user_token = userToken
        self.stream_sync_announcer = None
        self._main_prx_ = None
        self._auth_prx_ = None

        try:
            self._fd_ = open(filename, "rb") # pylint: disable=bad-option-value
        except FileNotFoundError:
            print("Archivo no encontrado: " + filename)

    def update_main(self):
        ''' Consigue un Main Service '''
        self._main_prx_ = random.choice(list(self.announcements_listener.mains.values()))

    def update_auth(self):
        ''' Consigue un Authenticator Service '''
        self._auth_prx_ = self._main_prx_.getAuthenticator()

    def getSDP(self, userToken, port: int, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Retorna la configuracion del flujo SDP '''
        self.update_main()
        try:
            self.update_auth()
        except IceFlix.TemporaryUnavailable:
            print("[STREAM CONTROLLER] No se ha encontrado ningún servicio de Autenticación")
            return ''

        if not self._auth_prx_.isAuthorized(userToken):
            raise IceFlix.Unauthorized

        self._emitter_ = iceflixrtsp.RTSPEmitter(self._filename_, "127.0.0.1", port)
        self._emitter_.start()
        return self._emitter_.playback_uri

    def getSyncTopic(self, current=None): # pylint: disable=invalid-name,unused-argument
        """ Devuelve el ID correspondiente """

        return self.service_id

    def refreshAuthentication(self, user_token, current=None): # pylint: disable=unused-argument
        """ Actualiza el token de usuario """

        self.update_main()
        try:
            self.update_auth()
        except IceFlix.TemporaryUnavailable:
            print("[STREAM CONTROLLER] No se ha encontrado ningún servicio de Autenticación")
            return ''

        if not self._auth_prx_.isAuthorized(user_token):
            raise IceFlix.Unauthorized

        if self.authentication_timer.is_alive():
            self.authentication_timer.cancel()

        return None

    def stop(self, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Detiene la emision del flujo SDP '''

        self._emitter_.stop()
        current.adapter.remove(current.id)
        print("\n\nVideo parado y adaptador eliminado")
