#!/usr/bin/python3
# pylint: disable=invalid-name
''' Servicio de Catálogo, se encarga de listar los medios disponibles, persistentes
    y los anunciados por los Providers '''

import sqlite3
import sys
import json
from time import sleep
from os import path, rename
import IceStorm
import uuid
from stream_announcements import StreamAnnouncementsListener
from service_announcement import ServiceAnnouncementsListener, ServiceAnnouncementsSender
from catalog_updates import CatalogUpdatesListener, CatalogUpdatesSender
import Ice
SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")
DB_PATH = path.join(path.dirname(__file__), "media.db")
USERS_PATH = None
Ice.loadSlice(SLICE_PATH)
import IceFlix # pylint: disable=wrong-import-position

from media import MediaDB
from constants import ANNOUNCEMENT_TOPIC, ICESTORM_PROXY_PROPERTY, CATALOG_SYNC_TOPIC, STREAM_ANNOUNCES_TOPIC

class MediaCatalogI(IceFlix.MediaCatalog): # pylint: disable=inherit-non-class
    ''' Instancia del servicio de Catálogo '''

    def __init__(self):
        self._media_ = {}
        self._main_prx_ = None
        self._auth_prx_ = None
        self.service_id = str(uuid.uuid4())
        self.actualizado = False
        self._anunciamientos_sender = None
        self._anunciamientos_listener = None
        self._updates_sender = None
        self._stream_listener= None
        
    
    def read_media(self):
        conn = sqlite3.connect(DB_PATH)
        ddbb_cursor = conn.cursor()
        ddbb_cursor.execute("SELECT * FROM media")
        query = ddbb_cursor.fetchall()
        conn.close()
        if query:
            for media in query:
                info = IceFlix.MediaInfo(media[2], media[1].split())
                self._media_.update({media[0]: IceFlix.Media(media[0], None, info)})

    def add_media(self, media_id, initial_name, srv_id):
        if self.is_in_catalog(media_id):
            return
        info = IceFlix.MediaInfo(initial_name, [])
        provider_proxy = self.find_provider(srv_id)
        self._media_.update({media_id: IceFlix.Media(media_id, provider_proxy, info)})


    def remove_media(self, media_id):
        if self.is_in_catalog(media_id):
            return
        self._media_.pop(media_id)


    def find_provider(self, srv_id):
        return self._anunciamientos_listener.providers[srv_id]

    def get_users_tags(self, media):
        # TODO: llamar a algun authenticator activo y acceder a su base de datos para conseguir las tags del media
        USERS_PATH = self.update_user_path()

        user_tags = {}

        with open(USERS_PATH, "r", encoding="utf8") as file_descriptor:
            obj = json.load(file_descriptor)

        for i in obj["users"]:
            for j in i["tags"]:
                if media.name in j.keys():
                    user_tags.update({i["user"]: i["tags"]})

        return user_tags


    def getTile(self, mediaId: str, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Retorna un objeto Media con la informacion del medio con el ID dado '''

        # Buscar en medios tmeporales
        media = self._media_.get(mediaId)
        if media:
            provider = self._media_.get(mediaId).provider #  Preguntar esto
            if provider:
                try:
                    provider.ice_ping()
                except Ice.ConnectionRefusedException:
                    raise IceFlix.TemporaryUnavailable
                else:
                    return self._media_.get(mediaId)
            else:
                raise IceFlix.TemporaryUnavailable

        # Buscar ID en bbdd
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(f"SELECT * FROM media WHERE id LIKE '{mediaId}'") # pylint: disable=invalid-name,unused-argument

        query = c.fetchall()

        # Buscar el ID en bbdd y temporal
        if not query and mediaId not in self._media_.keys():
            raise IceFlix.WrongMediaId


    def getTilesByName(self, name: str, exact: bool, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Retorna una lista de IDs a partir del nombre dado'''

        id_list = []
        if exact:
            for media in self._media_.values():
                new_name = path.split(media.info.name)[1].lower()
                if name.lower().split(".")[0] == new_name.split(".")[0]:
                    id_list.append(media.mediaId)
        else:
            for media in self._media_.values():
                new_name = path.split(media.info.name)[1].lower()
                if name.lower().split(".")[0] in new_name.split(".")[0]:
                    id_list.append(media.mediaId)

        return id_list


    def getTilesByTags(self, tags: list, includeAllTags: bool, userToken, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Retorna una lista de IDs de los medios con las tags dadas '''

        try:
            username = self.check_user_name(userToken)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized
        else:

            list_returned = []
            id_list = []

            for media_id in self._media_:
                list_returned.append(media_id)

            with open(USERS_PATH, "r", encoding="utf8") as f:
                obj = json.load(f)
                for i in obj["users"]:
                    if i["user"] == username:
                        user_tags = i["tags"]

            if includeAllTags:
                valid = True
                for media_id in list_returned:
                    all_user_tags = user_tags.get(media_id)
                    if all_user_tags:
                        if len(all_user_tags) == len(tags):
                            for user_tag in all_user_tags:
                                if user_tag not in tags:
                                    valid = False
                            if valid:
                                id_list.append(media_id)
                                valid = True
            else:
                valid = False
                for media_id in list_returned:
                    all_user_tags = user_tags.get(media_id)
                    if all_user_tags:
                        for x in all_user_tags:
                            if x in tags:
                                valid = True
                                break
                        if valid:
                            id_list.append(media_id)
                            valid = False

            return id_list

    def addTags(self, mediaId: str, tags: list, userToken, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Añade las tags dadas al medio con el ID dado '''

        try:
            user_name = self.check_user_name(userToken)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized

        if mediaId not in self._media_:
            raise IceFlix.WrongMediaId

        self.add_tags(mediaId, tags, user_name)


    def removeTags(self, mediaId: str, tags: list, userToken, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Elimina las tags dadas del medio con el ID dado '''

        try:
            user_name = self.check_user_name(userToken)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized

        self.remove_tags(mediaId, tags, user_name)


    def renameTile(self, mediaId, name, adminToken, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Renombra el medio de la estructura correspondiente '''

        try:
            self.check_admin(adminToken)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized
        else:
            self.rename_tile(mediaId, name)


    def updateMedia(self, mediaId, initialName, provider, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Añade o actualiza el medio del ID dado '''

        info = IceFlix.MediaInfo(initialName, [])
        nuevo = IceFlix.Media(mediaId, provider, info)
        self._media_.update({mediaId: nuevo})


    def check_admin(self, admin_token: str):
        ''' Comprueba si un token es Administrador '''

        try:
            is_admin = self._main_prx_.isAdmin(admin_token)
            if not is_admin:
                raise IceFlix.Unauthorized
        except IceFlix.TemporaryUnavailable:
            raise IceFlix.Unauthorized
        else:
            return is_admin


    def check_user(self, user_token: str):
        ''' Comprueba que la sesion del usuario es la actual '''

        return self._auth_prx_.isAuthorized(user_token)


    def check_user_name(self, user_token: str):
        ''' Comprueba que la sesion del usuario es la actual '''

        try:
            user_name = self._auth_prx_.whois(user_token)
        except IceFlix.Unauthorized as e:
            raise e
        else:
            return user_name

    
    @property
    def get_mediaDB(self):
        
        medias = self._media_.items()

        mediaDBList = []

        for media in medias:
            media_id, mediaO = media
            media_info = mediaO.info
            media_name = media_info.name
            media_tags = self.get_users_tags(media)
            mediaDBList.append(MediaDB(media_id, media_name, media_tags))

        return mediaDBList

    def is_in_catalog(self, mediaId):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(f"SELECT * FROM media WHERE id LIKE '{mediaId}'") # pylint: disable=invalid-name,unused-argument

        query = c.fetchall()

        # Buscar el ID en bbdd y temporal
        if not query and mediaId not in self._media_.keys():
            return False
        return True

    def update_user_path(self):
        ''' Actualiza la ruta del json de usuarios usando el id de un authenticator disponible '''
        # Buscar authenticator disponible
        auths = self._anunciamientos_listener.authenticators.items()

        for auth in auths:
            auth_id, auth_prx = auth
            try:
                auth_prx.ice_ping()
                USERS_PATH = path.join(path.join(path.dirname(__file__),
                       "persistence"), (auth_id + "_users.json"))
                print(USERS_PATH)
                return USERS_PATH

            except Ice.ConnectionRefusedException:
                self._anunciamientos_listener.authenticators.remove(auth)

        raise IceFlix.TemporaryUnavailable


    def add_tags(self, media_id, tags, user):
        ''' Añade las tags indicadas al usuario y medio correspondiente '''

        self.update_user_path() # Buscar un authenticator disponible
        
        # Cambiar tags persistentes
        with open(USERS_PATH, "r", encoding="utf8") as file_descriptor:
            obj = json.load(file_descriptor)

        for i in obj["users"]:
            if i["user"] == user:
                actuales = i["tags"].get(media_id)
                if not actuales:
                    actuales = []
                for tag in tags:
                    actuales.append(tag)
                i["tags"].update({media_id:actuales})
                break

        with open(USERS_PATH, 'w', encoding="utf8") as file:
            json.dump(obj, file, indent=2)

    
    def remove_tags(self, media_id, tags, user):
        ''' Elimina las tags indicadas del usuario y medio correpondiente '''

        self.update_user_path() # Buscar un authenticator disponible

        # Cambiar tags persistentes
        with open(USERS_PATH, "r", encoding="utf8") as f:
            obj = json.load(f)

        for i in obj["users"]:
            if i["user"] == user:
                actuales = i["tags"].get(media_id)
                for tag in tags:
                    if tag in actuales:
                        actuales.remove(tag)
                i["tags"].update({media_id:actuales})
                break

        with open(USERS_PATH, 'w', encoding="utf8") as file:
            json.dump(obj, file, indent=2)

    
    def rename_tile(self, media_id, name):
        ''' Renombra el medio con el identificador dado al nuevo nombre '''

        # Buscar id en medios estáticos
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(f"SELECT * FROM media where id LIKE '{media_id}'")
        media = conn.commit()
        conn.close()

        # Buscar id en medios dinamicos
        if media_id not in self._media_ and not media:
            raise IceFlix.WrongMediaId

        # Cambiar media en medios dinamicos
        if media_id in self._media_:
            media = self._media_.get(media_id)
            #old_name = media.info.name # Si se hace esto no va a funcionar porque todos acceden al mismo archivo
            old_name = name             # El archivo ya ha cambiado de nombre porque lo hizo el otro Catalogo
            suffix = media.info.name.split(".")[1]
            media.info.name = name + "." + suffix
            self._media_.update({media_id: media})

        # Cambiar en directorio
        try:
            rename(old_name, "IceFlix/resources/" + name + "." + suffix)
        except FileNotFoundError:
            raise IceFlix.WrongMediaId

        # Buscar medio en bbdd
        try:
            in_ddbb = self.getTile(media_id)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized

        else:
            if in_ddbb:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute(
                    f"UPDATE media SET name = '{name}.mp4' WHERE id LIKE '{media_id}'")
                conn.commit()
                conn.close()


    def share_data_with(self, service, current=None):
        """Share the current database with an incoming service."""
        service.updateDB(self.get_mediaDB, self.service_id)


    def updateDB(self, values, service_id, current=None):  # pylint: disable=invalid-name,unused-argument
        """Receives the current main service database from a peer."""
        print(f"Receiving remote data base from {service_id} to {self.service_id}")
        
        for media in values:
            print("Se recibe el obejeto:")
            print(media)
            info = IceFlix.MediaInfo(media.name, media.tagsPerUser.values())
            self._media_.update({media.mediaId: IceFlix.Media(media.mediaId, None, info)})


class MediaCatalogServer(Ice.Application):
    ''' Servidor de Catálogo  '''

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
            self.proxy,
        )

        self.subscriber = ServiceAnnouncementsListener(
            self.servant, self.servant.service_id, IceFlix.MediaCatalogPrx
        )

        subscriber_prx = self.adapter.addWithUUID(self.subscriber)
        topic.subscribeAndGetPublisher({}, subscriber_prx)

    def setup_catalog_updates(self):
        """Configure the announcements sender and listener."""

        communicator = self.communicator()
        topic_manager = IceStorm.TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager")
        )

        try:
            topic = topic_manager.create(CATALOG_SYNC_TOPIC)
        except IceStorm.TopicExists:
            topic = topic_manager.retrieve(CATALOG_SYNC_TOPIC)

        self._updates_sender = ServiceAnnouncementsSender(
            topic,
            self.servant.service_id,
            self.proxy,
        )

        self._updates_listener = ServiceAnnouncementsListener(
            self.servant, self.servant.service_id, IceFlix.MediaCatalogPrx
        )

        subscriber_prx = self.adapter.addWithUUID(self._updates_listener)
        topic.subscribeAndGetPublisher({}, subscriber_prx)


    def setup_stream_announcements(self):
        '''  Configurar listener del topic StreamAnnouncements '''

        communicator = self.communicator()
        topic_manager = IceStorm.TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager")
        )
        try:
            topic = topic_manager.create(STREAM_ANNOUNCES_TOPIC)
        except IceStorm.TopicExists:
            topic = topic_manager.retrieve(STREAM_ANNOUNCES_TOPIC)
            
        self._stream_listener = StreamAnnouncementsListener(
            self.servant, self.servant.service_id, IceFlix.MediaCatalogPrx)
        
        subscriber_prx = self.adapter.addWithUUID(self._stream_listener)
        topic.subscribeAndGetPublisher({}, subscriber_prx)


    def run(self, argv):
        sleep(1)

        broker = self.communicator()
        self.servant = MediaCatalogI()

        self.adapter = broker.createObjectAdapterWithEndpoints('MediaCatalogAdapter', 'tcp')
        media_catalog_proxy = self.adapter.addWithUUID(self.servant)

        self.proxy = media_catalog_proxy
        self.adapter.activate()

        self.setup_announcements()
        self.setup_catalog_updates()
        self.setup_stream_announcements()

        self.servant._anunciamientos_sender = self.announcer
        self.servant._anunciamientos_listener = self.subscriber
        self.servant._updates_sender = self._updates_sender
        self.servant._stream_listener = self._stream_listener

        sleep(6)
        self.servant.read_media()
        self.announcer.start_service()

        #print(self.servant._media_)
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        self.announcer.stop()

if __name__ == '__main__':
    # MediaCatalogServer().run(sys.argv)
    sys.exit(MediaCatalogServer().main(sys.argv))
