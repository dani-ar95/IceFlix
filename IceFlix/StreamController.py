#!/usr/bin/python3
# pylint: disable=invalid-name
''' Clase que se encarga del control del streaming, sus instancias cargan un video
     y retornan la uri del streaming '''

from os import path
from random import random
import sys
import uuid
import Ice
import IceStorm
import iceflixrtsp # pylint: disable=import-error
from service_announcement import ServiceAnnouncementsListener, ServiceAnnouncementsSender
from user_revocations import RevocationsListener, RevocationsSender
from stream_sync import StreamSyncListener, StreamSyncSender
from constants import STREAM_SYNC_TOPIC, REVOCATIONS_TOPIC

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")
Ice.loadSlice(SLICE_PATH)
import IceFlix # pylint: disable=wrong-import-position

class StreamControllerI(IceFlix.StreamController): # pylint: disable=inherit-non-class
    ''' Instancia de StreamController '''

    def __init__(self, announcements_listener, file_path, current=None): # pylint: disable=invalid-name,unused-argument
        self._emitter_ = None
        self._filename_ = file_path
        self.service_id = str(uuid.uuid4)
        self.announcements_listener = announcements_listener
        self.authentication_timer = None
        
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

    def getSyncTopic(self, current=None):
        return self.service_id

    def refreshAuthentication(self, user_token, current=None):
        main_prx = random.choice(list(self.announcements_listener.mains.values()))
        try:
            auth = main_prx.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            print("[STREAM CONTROLLER] No se ha encontrado ningún servicio de Autenticación")
            return
        
        if not auth.isAuthorized(user_token):
           raise IceFlix.Unauthorized
       
        if self.authentication_timer.is_alive():
            self.authentication_timer.cancel()

    def stop(self, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Detiene la emision del flujo SDP '''
        self._emitter_.stop()
        current.adapter.remove(current.id)

    def check_user(self, user_token):
        ''' Comprueba que la sesion del usuario está actualizada '''

        is_user = self._authenticator_prx_.isAuthorized(user_token)
        if not is_user:
            raise IceFlix.Unauthorized
        return is_user

    # def share_data_with(self, service):
    #     """Share the current database with an incoming service."""
    #     service.updateDB(None, self.service_id)

    # def updateDB(
    #     self, values, service_id, current
    # ):  # pylint: disable=invalid-name,unused-argument
    #     """Receives the current main service database from a peer."""
    #     print(
    #         "Receiving remote data base from %s to %s", service_id, self.service_id
    #     )

class StreamControllerServer(Ice.Application): # pylint: disable=invalid-name
    ''' Servidor del controlador de Streaming '''

    # def setup_announcements(self):
    #     """Configure the announcements sender and listener."""

    #     communicator = self.communicator()
    #     topic_manager = IceStorm.TopicManagerPrx.checkedCast(
    #         communicator.propertyToProxy("IceStorm.TopicManager")
    #     )

    #     try:
    #         topic = topic_manager.create(ANNOUNCEMENT_TOPIC)
    #     except IceStorm.TopicExists:
    #         topic = topic_manager.retrieve(ANNOUNCEMENT_TOPIC)

    #     self.announcer = ServiceAnnouncementsSender(
    #         topic,
    #         self.servant.service_id,
    #         self.proxy,
    #     )

    #     self.subscriber = ServiceAnnouncementsListener(
    #         self.servant, self.servant.service_id, IceFlix.StreamControllerPrx
    #     )

    #     subscriber_prx = self.adapter.addWithUUID(self.subscriber)
    #     topic.subscribeAndGetPublisher({}, subscriber_prx)

    def setup_revocations(self):
        communicator = self.communicator()
        topic_manager = IceStorm.TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager")
        )

        try:
            topic = topic_manager.create(REVOCATIONS_TOPIC)
        except IceStorm.TopicExists:
            topic = topic_manager.retrieve(REVOCATIONS_TOPIC)

        self.revocations_announcer = RevocationsSender(
            topic,
            self.servant.service_id,
            self.proxy,
        )

        self.revocations_subscriber = RevocationsListener(
            self.servant, self.servant.service_id, IceFlix.StreamControllerPrx
        )

        subscriber_prx = self.adapter.addWithUUID(self.revocations_subscriber)
        topic.subscribeAndGetPublisher({}, subscriber_prx)
        
    def setup_sync(self):
        communicator = self.communicator()
        topic_manager = IceStorm.TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager")
        )

        try:
            topic = topic_manager.create(STREAM_SYNC_TOPIC)
        except IceStorm.TopicExists:
            topic = topic_manager.retrieve(STREAM_SYNC_TOPIC)

        self.stream_sync_announcer = StreamSyncSender(
            topic,
            self.servant.service_id,
            self.proxy,
        )

        self.stream_sync_subscriber = StreamSyncListener(
            self.servant, self.servant.service_id, IceFlix.StreamControllerPrx
        )

        subscriber_prx = self.adapter.addWithUUID(self.revocations_subscriber)
        topic.subscribeAndGetPublisher({}, subscriber_prx)

    def run(self, args): # pylint: disable=unused-argument

            #Suscribir el Controller al topic Revocations (listener)
            #Suscribir el Controller al topic StreamSync(subscriber/listener)
            #Cuando reciba un revokeToken llamar al subscriber del topic StreamSync y lanzar requestAuthentication
            #Escuchar en topic StreamSync durante 5 segundos:
                #Si no hay respuesta, cortar reproduccion
                #Si hay respuesta, comprobar el token


        self.servant = StreamControllerI()
        broker = self.communicator()

        self.adapter = broker.createObjectAdapterWithEndpoints(
            'StreamControllerAdapter', 'tcp')
        self.proxy = self.adapter.addWithUUID(self.servant)
        self.adapter.activate()

        # self.setup_announcements()
        self.setup_revocations()
        self.setup_sync()

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        self.announcer.stop()

if __name__ == '__main__':
    sys.exit(StreamControllerServer().main(sys.argv))
