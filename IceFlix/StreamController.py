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

    def share_data_with(self, service):
        """Share the current database with an incoming service."""
        service.updateDB(None, self.service_id)

    def updateDB(
        self, values, service_id, current
    ):  # pylint: disable=invalid-name,unused-argument
        """Receives the current main service database from a peer."""
        print(
            "Receiving remote data base from %s to %s", service_id, self.service_id
        )

class StreamControllerServer(Ice.Application): # pylint: disable=invalid-name
    ''' Servidor del controlador de Streaming '''

    def setup_announcements(self):
        """Configure the announcements sender and listener."""

        communicator = self.communicator()
        topic_manager = IceStorm.TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager")
        )

        try:
            topic = topic_manager.create("ServiceAnnouncements")
        except IceStorm.TopicExists:
            topic = topic_manager.retrieve("ServiceAnnouncements")

        self.announcer = ServiceAnnouncementsSender(
            topic,
            self.servant.service_id,
            self.proxy,
        )

        self.subscriber = ServiceAnnouncementsListener(
            self.servant, self.servant.service_id, IceFlix.StreamControllerPrx
        )

        subscriber_prx = self.adapter.addWithUUID(self.subscriber)
        topic.subscribeAndGetPublisher({}, subscriber_prx)

    def run(self, args): # pylint: disable=unused-argument
        ''' No hace mucho '''

        broker = self.communicator()

        self.setup_announcements()
        self.announcer.start_service()

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        self.announcer.stop()

if __name__ == '__main__':
    sys.exit(StreamControllerServer().main(sys.argv))
