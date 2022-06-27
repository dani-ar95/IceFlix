#!/usr/bin/python3
# pylint: disable=invalid-name
''' Clase que se encarga del control del streaming, sus instancias cargan un video
     y retornan la uri del streaming '''

from os import path
import random
import uuid
import Ice
from IceStorm import TopicManagerPrx, TopicExists # pylint: disable=no-name-in-module
import iceflixrtsp # pylint: disable=import-error
from service_announcement import ServiceAnnouncementsListener, ServiceAnnouncementsSender
from user_revocations import RevocationsListener, RevocationsSender
from stream_sync import StreamSyncListener, StreamSyncSender
from constants import STREAM_SYNC_TOPIC, REVOCATIONS_TOPIC # pylint: disable=no-name-in-module

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")
Ice.loadSlice(SLICE_PATH)
import IceFlix # pylint: disable=wrong-import-position

class StreamControllerI(IceFlix.StreamController): # pylint: disable=inherit-non-class
    ''' Instancia de StreamController '''

    def __init__(self, announcements_listener, filename, userToken, current=None): # pylint: disable=invalid-name,unused-argument
        self._emitter_ = None
        self._filename_ = filename
        self.service_id = str(uuid.uuid4)
        self.announcements_listener = announcements_listener
        self.authentication_timer = None
        self.user_token = userToken

        try:
            self._fd_ = open(filename, "rb") # pylint: disable=bad-option-value
        except FileNotFoundError:
            print("Archivo no encontrado: " + filename)

    def getSDP(self, userToken, port: int, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Retorna la configuracion del flujo SDP '''
        main_prx = random.choice(list(self.announcements_listener.mains.values()))
        try:
            auth = main_prx.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            print("[STREAM CONTROLLER] No se ha encontrado ningún servicio de Autenticación")
            return ''

        if not auth.isAuthorized(userToken):
            raise IceFlix.Unauthorized

        self._emitter_ = iceflixrtsp.RTSPEmitter(self._filename_, "127.0.0.1", port)
        self._emitter_.start()
        return self._emitter_.playback_uri

    def getSyncTopic(self, current=None): # pylint: disable=invalid-name,unused-argument
        """ Devuelve el ID correspondiente """

        return self.service_id

    def refreshAuthentication(self, user_token, current=None): # pylint: disable=unused-argument
        """ Actualiza el token de usuario """

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


class StreamControllerServer(Ice.Application): # pylint: disable=invalid-name
    ''' Servidor del controlador de Streaming '''

    def __init__(self, announcements_listener, filename, userToken):
        """ Inicializa el controlador """

        super().__init__()
        self.servant = StreamControllerI(announcements_listener, filename, userToken)
        self.adapter = None
        self.proxy = None
        self.revocations_announcer = None
        self.revocations_subscriber = None
        self.stream_sync_announcer = None
        self.revocations_announcer = None
        self.stream_sync_subscriber = None

    def setup_revocations(self):
        """ Establece la interfaz para el topic UserRovocations """

        communicator = self.communicator()
        topic_manager = TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager")
        )

        try:
            topic = topic_manager.create(REVOCATIONS_TOPIC)
        except TopicExists:
            topic = topic_manager.retrieve(REVOCATIONS_TOPIC)

        self.revocations_announcer = RevocationsSender(
            topic,
            self.servant.service_id,
            self.proxy,
        )

        self.revocations_subscriber = RevocationsListener(
            self.servant, self.proxy, self.servant.service_id, IceFlix.StreamControllerPrx
        )

        subscriber_prx = self.adapter.addWithUUID(self.revocations_subscriber)
        topic.subscribeAndGetPublisher({}, subscriber_prx)

    def setup_sync(self):
        """ Permite pausar el stream """

        communicator = self.communicator()
        topic_manager = TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager")
        )

        try:
            topic = topic_manager.create(STREAM_SYNC_TOPIC)
        except TopicExists:
            topic = topic_manager.retrieve(STREAM_SYNC_TOPIC)

        self.stream_sync_announcer = StreamSyncSender(topic)

        self.stream_sync_subscriber = StreamSyncListener(self.servant)

        subscriber_prx = self.adapter.addWithUUID(self.revocations_subscriber)
        topic.subscribeAndGetPublisher({}, subscriber_prx)

    def run(self, args):

        self.servant = StreamControllerI() # pylint: disable=no-value-for-parameter
        broker = self.communicator()

        self.adapter = broker.createObjectAdapterWithEndpoints(
            'StreamControllerAdapter', 'tcp')
        self.proxy = self.adapter.addWithUUID(self.servant)
        self.adapter.activate()

        self.setup_revocations()
        self.setup_sync()

        self.shutdownOnInterrupt()
        broker.waitForShutdown()
