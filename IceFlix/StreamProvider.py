#!/usr/bin/python3
# pylint: disable=invalid-name
''' Servicio de Streaming '''

from os import path, remove
import hashlib
import glob
import sys
from time import sleep
import threading
import uuid
import Ice
import IceStorm
from service_announcement import ServiceAnnouncementsListener, ServiceAnnouncementsSender
from stream_announcements import StreamAnnouncementsSender, StreamAnnouncementsListener
from constants import ANNOUNCEMENT_TOPIC, STREAM_ANNOUNCES_TOPIC

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")

Ice.loadSlice(SLICE_PATH)
import IceFlix # pylint: disable=wrong-import-position

from StreamController import StreamControllerI # pylint: disable=import-error, wrong-import-position

class StreamProviderI(IceFlix.StreamProvider): # pylint: disable=inherit-non-class
    ''' Instancia de Stream Provider '''

    def __init__(self):
        self._provider_media_ = {}
        self._proxy_ = None
        self._stream_announcements_sender = None
        self.service_id = str(uuid.uuid4())

    def getStream(self, mediaId: str, userToken: str, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Factoría de objetos StreamController '''

        try:
            self.check_user(userToken)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized

        else:
            asked_media = None
            if self.isAvailable(mediaId):
                provide_media = self._provider_media_.get(mediaId)
            else:
                try:
                    asked_media = self._catalog_prx_.getTile(mediaId)
                except IceFlix.WrongMediaId:
                    raise IceFlix.WrongMediaId

            if asked_media:
                provide_media = asked_media
            else:
                name = provide_media.info.name
                servant = StreamControllerI(name)
                servant._authenticator_prx_ = self._authenticator_prx_
                proxy = current.adapter.addWithUUID(servant)
                return IceFlix.StreamControllerPrx.checkedCast(proxy)


    def isAvailable(self, mediaId: str, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Confirma si existe un medio con ese id'''

        return mediaId in self._provider_media_

    def uploadMedia(self, fileName: str, uploader, adminToken: str, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Permite al administador subir un archivo al sistema '''

        try:
            self.check_admin(adminToken)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized
        else:
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
            else:
                id_hash = hashlib.sha256(new_file).hexdigest()

                file = path.split(fileName)[1]
                new_file_name = path.join(path.dirname(__file__), "resources/" + file)

                with open(new_file_name, "wb") as write_pointer:
                    write_pointer.write(new_file)

                # Crear el media propio
                info = IceFlix.MediaInfo(new_file_name, [])
                new_media = IceFlix.Media(id_hash, self._proxy_, info)
                self._provider_media_.update({id_hash:new_media})

                # Enviar medio al catálogo
                self._catalog_prx_.updateMedia(id_hash, fileName, self._proxy_)

                return id_hash

    def deleteMedia(self, mediaId: str, adminToken: str, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Perimite al administrador borrar archivos conociendo su id '''

        self.update_directory()
        try:
            self.check_admin(adminToken)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized

        if mediaId in self._provider_media_:
            filename = self._provider_media_.get(mediaId).info.name
        else:
            try:
                media_file = self._catalog_prx_.getTile(mediaId)
            except IceFlix.WrongMediaId:
                raise IceFlix.WrongMediaId
            else:
                filename = media_file.info.name
        remove(filename)

    def update_directory(self):
        root_folder = path.join(path.dirname(__file__), "resources")
        candidates = glob.glob(path.join(root_folder, '*'), recursive=True)


        for filename in candidates:
            with open("./"+str(filename), "rb") as f:
                read_file = f.read()
                id_hash = hashlib.sha256(read_file).hexdigest()
                new_media = IceFlix.Media(id_hash, self._proxy_, IceFlix.MediaInfo(filename, []))
                self._provider_media_.update({id_hash: new_media})

            self._catalog_prx_.updateMedia(id_hash, filename, self._proxy_)

    def check_admin(self, admin_token: str): # Actualizar funcion
        ''' Comprueba si un token es Administrador '''

        is_admin = self._main_prx_.isAdmin(admin_token)
        if not is_admin:
            raise IceFlix.Unauthorized
        return is_admin

    def check_user(self, user_token: str):
        ''' Comprueba que la sesion del usuario es la actual '''

        is_user = self._authenticator_prx_.isAuthorized(user_token)
        if not is_user:
            raise IceFlix.Unauthorized
        else:
            return is_user

    def share_data_with(self, service):
        """Share the current database with an incoming service."""
        service.updateDB(None, self.service_id)

class StreamProviderServer(Ice.Application):
    ''' Servidor que comparte con el catálogo sus medios disponibles  '''

    def __init__(self):
        super().__init__()
        self.servant = StreamProviderI()
        self.adapter = None
        self.subscriber = None
        self.announcer = None
        self.stream_announcements_announcer = None

    def setup_announcements(self):
        """Configure the announcements sender and listener."""

        communicator = self.communicator()
        topic_manager = IceStorm.TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager")
        )

        try:
            topic = topic_manager.create(ANNOUNCEMENT_TOPIC)
        except IceStorm.TopicExists:
            topic = topic_manager.retrieve(ANNOUNCEMENT_TOPIC)

        self.announcer = ServiceAnnouncementsSender(
            topic,
            self.servant.service_id,
            self.servant._proxy_,
        )

        self.subscriber = ServiceAnnouncementsListener(
            self.servant, self.servant.service_id, IceFlix.StreamProviderPrx
        )

        subscriber_prx = self.adapter.addWithUUID(self.subscriber)
        topic.subscribeAndGetPublisher({}, subscriber_prx)


    def setup_stream_announcements(self):
        """Configuracion topic StreamAnnouncements

            TODO: Revisar
        """
        
        communicator = self.communicator()
        topic_manager = IceStorm.TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager")
        )

        try:
            topic = topic_manager.create(STREAM_ANNOUNCES_TOPIC)
        except IceStorm.TopicExists:
            topic = topic_manager.retrieve(STREAM_ANNOUNCES_TOPIC)

        self.stream_announcements_announcer = StreamAnnouncementsSender(
            topic,
            self.servant.service_id,
            self.servant._proxy_,
        )

        self.stream_announcements_listener = StreamAnnouncementsListener(
            self.servant, self.servant.service_id, IceFlix.StreamProviderPrx
        )

        subscriber_prx = self.adapter.addWithUUID(self.stream_announcements_listener)
        subscriber_prx = topic.getPublisher()
    
    def run(self, argv):
        '''' Inicialización de la clase '''

        broker = self.communicator()

        self.servant = StreamProviderI()
        self.adapter = broker.createObjectAdapterWithEndpoints('StreamProviderAdapter', 'tcp')
        stream_provider_proxy = self.adapter.addWithUUID(self.servant)

        self.servant._proxy_ = stream_provider_proxy
        self.adapter.activate()

        self.setup_announcements()
        self.setup_stream_announcements()

        self.servant._stream_announcements_sender = self.stream_announcements_announcer

        self.announcer.start_service()        

        root_folder = path.join(path.dirname(__file__), "resources")
        candidates = glob.glob(path.join(root_folder, '*'), recursive=True)
    
        sleep(5)
        
        for filename in candidates:
            with open("./"+str(filename), "rb") as f:
                read_file = f.read()
                id_hash = hashlib.sha256(read_file).hexdigest()
                new_media = IceFlix.Media(id_hash, stream_provider_proxy, IceFlix.MediaInfo(filename, []))
                self.servant._provider_media_.update({id_hash: new_media})

            self.stream_announcements_announcer.newMedia(id_hash, filename)

        #self.servant._stream_announcements_sender.newMedia("IDENTIFICADOR", "NOMBRE")

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        self.announcer.stop()

if __name__ == '__main__':
    sys.exit(StreamProviderServer().main(sys.argv))
