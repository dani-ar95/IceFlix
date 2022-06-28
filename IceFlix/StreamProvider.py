#!/usr/bin/python3
# pylint: disable=invalid-name
''' Servicio de Streaming '''

from os import path, remove
import hashlib
import glob
import random
import sys
import uuid
import Ice
from IceStorm import TopicManagerPrx, TopicExists # pylint: disable=no-name-in-module
from user_revocations import RevocationsListener, RevocationsSender # pylint: disable=no-name-in-module
from service_announcement import ServiceAnnouncementsListener, ServiceAnnouncementsSender
from stream_announcements import StreamAnnouncementsSender, StreamAnnouncementsListener
from stream_sync import StreamSyncSender, StreamSyncListener
from constants import ANNOUNCEMENT_TOPIC, REVOCATIONS_TOPIC # pylint: disable=no-name-in-module
from constants import STREAM_ANNOUNCES_TOPIC, STREAM_SYNC_TOPIC # pylint: disable=no-name-in-module

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")

Ice.loadSlice(SLICE_PATH)
import IceFlix # pylint: disable=wrong-import-position

from StreamController import StreamControllerI # pylint: disable=import-error, wrong-import-position

class StreamProviderI(IceFlix.StreamProvider): # pylint: disable=inherit-non-class,too-many-instance-attributes
    ''' Instancia de Stream Provider '''

    def __init__(self, broker):
        self._provider_media_ = {}
        self._proxy_ = None
        self._stream_announcements_sender = None
        self._service_announcer_listener = None
        self.service_id = str(uuid.uuid4())
        self._main_prx_ = None
        self._auth_prx_ = None
        self.broker = broker

    def update_main(self):
        ''' Consigue un Main Service '''
        self._main_prx_ = random.choice(list(self._service_announcer_listener.mains.values()))

    def update_auth(self):
        ''' Consigue un Authenticator Service '''
        self._auth_prx_ = self._main_prx_.getAuthenticator()

    def getStream(self, mediaId: str, userToken: str, current=None): # pylint: disable=invalid-name,unused-argument,too-many-locals
        ''' Factoría de objetos StreamController '''
        self.update_main()
        try:
            self.update_auth()
        except IceFlix.TemporaryUnavailable:
            print("[STREAM PROVIDER] No se ha encontrado ningún servicio de Autenticación")
            return ''

        if not self._auth_prx_.isAuthorized(userToken):
            raise IceFlix.Unauthorized

        if self.isAvailable(mediaId):
            asked_media = self._provider_media_.get(mediaId)
            name = asked_media.info.name
            controller = StreamControllerI(self._service_announcer_listener, name, userToken)
            controller_proxy = current.adapter.addWithUUID(controller)

            topic_manager = TopicManagerPrx.checkedCast(
                self.broker.propertyToProxy("IceStorm.TopicManager"))

            try:
                topic = topic_manager.create(REVOCATIONS_TOPIC)
            except TopicExists:
                topic = topic_manager.retrieve(REVOCATIONS_TOPIC)

            revocations_sender = RevocationsSender(
                topic, controller.service_id, controller_proxy)
            revocations_listener = RevocationsListener(
                controller, controller_proxy, controller.service_id, IceFlix.StreamControllerPrx
            )
            rev_subscriber_prx = current.adapter.addWithUUID(revocations_listener)
            topic.subscribeAndGetPublisher({}, rev_subscriber_prx)


            try:
                topic = topic_manager.create(STREAM_SYNC_TOPIC)
            except TopicExists:
                topic = topic_manager.retrieve(STREAM_SYNC_TOPIC)

            stream_sync_sender = StreamSyncSender(topic)
            stream_sync_listener = StreamSyncListener(controller, controller_proxy)

            sync_subscriber_prx = current.adapter.addWithUUID(stream_sync_listener)
            topic.subscribeAndGetPublisher({}, sync_subscriber_prx)
            controller.stream_sync_announcer = stream_sync_sender
            return IceFlix.StreamControllerPrx.checkedCast(controller_proxy)

        raise IceFlix.WrongMediaId(mediaId)

    def isAvailable(self, mediaId: str, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Confirma si existe un medio con ese id'''

        return mediaId in self._provider_media_

    def uploadMedia(self, fileName: str, uploader, adminToken: str, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Permite al administador subir un archivo al sistema '''
        self.update_main()
        if not self._main_prx_.isAdmin(adminToken):
            raise IceFlix.Unauthorized

        new_file = b""
        received = b""

        try:
            while True:
                received = uploader.receive(512)
                if not received:
                    break
                new_file += received
        except:
            raise IceFlix.UploadError

        if not new_file:
            raise IceFlix.UploadError

        id_hash = hashlib.sha256(new_file).hexdigest()

        file = path.split(fileName)[1]
        new_file_name = path.join(path.dirname(__file__), "resources/" + file)

        with open(new_file_name, "wb") as write_pointer:
            write_pointer.write(new_file)

        # Crear el media propio
        info = IceFlix.MediaInfo(new_file_name, [])
        new_media = IceFlix.Media(id_hash, self._proxy_, info)
        self._provider_media_.update({id_hash:new_media})

        # Anunciar medio
        self._stream_announcements_sender.newMedia(id_hash, new_file_name) #pylint: disable=too-many-function-args

        return id_hash

    def deleteMedia(self, mediaId: str, adminToken: str, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Perimite al administrador borrar archivos conociendo su id '''

        self.update_directory() #?
        self.update_main()
        if not self._main_prx_.isAdmin(adminToken):
            raise IceFlix.Unauthorized

        # Los catalogos tienen los medios que tengan los providers?
        if mediaId in self._provider_media_:
            filename = self._provider_media_.get(mediaId).info.name
            remove(filename)
            self._provider_media_.pop(mediaId)
            self._stream_announcements_sender.removedMedia(mediaId)
        else:
            raise IceFlix.WrongMediaId(mediaId)

    def reannounceMedia(self, srvId, current=None):
        """" Vuelve a anunciar todos los medios """

        if srvId not in self._service_announcer_listener.known_ids:
            raise IceFlix.UnknownService

        for entry in self._provider_media_:
            media = self._provider_media_.get(entry)
            print(f"[PROVIDER] ID: {self.service_id} Reanunciando {media.info.name}")
            self._stream_announcements_sender.newMedia(media.mediaId, media.info.name)

    def update_directory(self):
        """ Actualiza el directorio correspondiente """

        root_folder = path.join(path.dirname(__file__), "resources")
        candidates = glob.glob(path.join(root_folder, '*'), recursive=True)

        for filename in candidates:
            with open("./"+str(filename), "rb") as f:
                read_file = f.read()
                id_hash = hashlib.sha256(read_file).hexdigest()
                new_media = IceFlix.Media(id_hash, self._proxy_, IceFlix.MediaInfo(filename, []))
                self._provider_media_.update({id_hash: new_media})


class StreamProviderServer(Ice.Application):
    ''' Servidor que comparte con el catálogo sus medios disponibles  '''

    def __init__(self):
        super().__init__()
        self.servant_provider = None
        self.adapter = None
        self.subscriber = None
        self.announcer = None
        self.stream_announcements_announcer = None
        self.stream_announcements_listener = None

    def setup_announcements(self):
        """Configure the announcements sender and listener."""

        communicator = self.communicator()
        topic_manager = TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager")
        )

        try:
            topic = topic_manager.create(ANNOUNCEMENT_TOPIC)
        except TopicExists:
            topic = topic_manager.retrieve(ANNOUNCEMENT_TOPIC)

        self.announcer = ServiceAnnouncementsSender(
            topic,
            self.servant_provider.service_id,
            self.servant_provider._proxy_, #pylint: disable=protected-access
        )

        self.subscriber = ServiceAnnouncementsListener(
            self.servant_provider, self.servant_provider.service_id, IceFlix.StreamProviderPrx
        )

        subscriber_prx = self.adapter.addWithUUID(self.subscriber)
        topic.subscribeAndGetPublisher({}, subscriber_prx)


    def setup_stream_announcements(self):
        """Configuracion topic StreamAnnouncements

            TODO: Revisar
        """

        communicator = self.communicator()
        topic_manager = TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager")
        )

        try:
            topic = topic_manager.create(STREAM_ANNOUNCES_TOPIC)
        except TopicExists:
            topic = topic_manager.retrieve(STREAM_ANNOUNCES_TOPIC)

        self.stream_announcements_announcer = StreamAnnouncementsSender(
            topic,
            self.servant_provider.service_id,
            self.servant_provider._proxy_, #pylint: disable=protected-access
        )

        self.stream_announcements_listener = StreamAnnouncementsListener(
            self.servant_provider, self.servant_provider.service_id, IceFlix.StreamProviderPrx
        )

        subscriber_prx = self.adapter.addWithUUID(self.stream_announcements_listener)
        subscriber_prx = topic.getPublisher()

    def run(self, args):
        '''' Inicialización de la clase '''

        broker = self.communicator()
        self.servant_provider = StreamProviderI(broker)
        self.adapter = broker.createObjectAdapterWithEndpoints('StreamProviderAdapter', 'tcp')
        self.adapter.activate()
        self.adapter.add(self.servant_provider, broker.stringToIdentity("StreamProvider"))
        stream_provider_proxy = self.adapter.add(self.servant_provider,
                                                 Ice.stringToIdentity("ProviderPrincipal"))

        self.servant_provider._proxy_ = stream_provider_proxy #pylint: disable=protected-access

        print(f"[PROXY PROVIDER] {self.servant_provider._proxy_ }") #pylint: disable=protected-access
        self.setup_announcements()
        self.setup_stream_announcements()

        self.servant_provider._service_announcer_listener = self.subscriber #pylint: disable=protected-access
        self.servant_provider._stream_announcements_sender = self.stream_announcements_announcer #pylint: disable=protected-access

        self.announcer.start_service()
        root_folder = path.join(path.dirname(__file__), "resources")
        candidates = glob.glob(path.join(root_folder, '*'), recursive=True)

        for filename in candidates:
            with open("./"+str(filename), "rb") as f:
                read_file = f.read()
                id_hash = hashlib.sha256(read_file).hexdigest()
                new_media = IceFlix.Media(id_hash, stream_provider_proxy,
                                          IceFlix.MediaInfo(filename, []))
                self.servant_provider._provider_media_.update({id_hash: new_media}) #pylint: disable=protected-access

            self.stream_announcements_announcer.newMedia(id_hash, filename)

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        self.announcer.stop()

if __name__ == '__main__':
    sys.exit(StreamProviderServer().main(sys.argv))
