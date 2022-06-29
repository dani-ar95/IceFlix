#!/usr/bin/python3
# pylint: disable=invalid-name
''' Servicio de Catálogo, se encarga de listar los medios disponibles, persistentes
    y los anunciados por los Providers '''

import sqlite3
import sys
from time import sleep
from os import path, rename
import glob
import uuid
import random
import Ice
from IceStorm import TopicManagerPrx, TopicExists # pylint: disable=no-name-in-module
from constants import ANNOUNCEMENT_TOPIC, CATALOG_SYNC_TOPIC, STREAM_ANNOUNCES_TOPIC # pylint: disable=no-name-in-module
from stream_announcements import StreamAnnouncementsListener
from service_announcement import ServiceAnnouncementsListener, ServiceAnnouncementsSender
from catalog_updates import CatalogUpdatesListener, CatalogUpdatesSender
from media import MediaDB
SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")
DB_PATH = path.join(path.dirname(__file__), "media.db")
USERS_PATH = "IceFlix/users.json"
RESOURCES_FOLDER = path.join(path.dirname(__file__), "resources/")

Ice.loadSlice(SLICE_PATH)
try:
    import IceFlix
except ImportError:
    Ice.loadSlice(path.join(path.dirname(__file__), "iceflix.ice"))
    import IceFlix # pylint: disable=wrong-import-position


class MediaCatalogI(IceFlix.MediaCatalog): # pylint: disable=inherit-non-class, too-many-instance-attributes, too-many-public-methods
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
        self._stream_listener = None
        self._broker = None

    def read_media(self): # Actualizado
        """ Rellena los medios dinámicos utilizando la bbdd """

        conn = sqlite3.connect(DB_PATH)
        ddbb_cursor = conn.cursor()
        ddbb_cursor.execute("SELECT * FROM media")
        query = ddbb_cursor.fetchall()
        conn.close()
        if query:
            for media in query:
                tags = media[3]
                if tags:
                    info = IceFlix.MediaInfo(media[1], media[3].split(","))
                else:
                    info = IceFlix.MediaInfo(media[1], [])
                self._media_.update({media[0]: IceFlix.Media(media[0], media[4], info)})

    def add_media(self, media_id, initial_name, srv_id):
        """ Inserta un media en la bbdd """
        if not self.is_in_catalog(media_id):
            #Añadir medio en bbdd
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(f"""INSERT INTO media (media_id, media_name)
                    VALUES ('{media_id}','{initial_name}')""")
            conn.commit()
            conn.close()

        #Añadir medio en local
        info = IceFlix.MediaInfo(initial_name, [])
        provider_proxy = self.find_provider(srv_id)
        self._media_.update({media_id: IceFlix.Media(media_id, provider_proxy, info)})

    def remove_media(self, media_id):
        """ Elimina un media de la lista dinámica """

        if self.is_in_catalog(media_id):
            self._media_.pop(media_id)

    def find_provider(self, srv_id):
        """ Devuelve el provider con el identificador dado """

        return self._anunciamientos_listener.providers[srv_id]

    def get_users_tags(self, media): # Actualizado
        """ Devuelve un objeto TagsPerUser"""

        users_tags = {}

        conn = sqlite3.connect(DB_PATH)
        ddbb_cursor = conn.cursor()
        ddbb_cursor.execute(f"SELECT username, tags FROM media WHERE media_id='{media}'")
        conn.commit()
        query = ddbb_cursor.fetchall()
        conn.close()
        print(query)
        for info in query:
            if info[0] is not None:
                users_tags.update({info[0]: info[1].split(",")})

        return users_tags

    def update_main(self):
        ''' Consigue un Main Service '''
        self._main_prx_ = random.choice(list(self._anunciamientos_listener.mains.values()))

    def update_auth(self):
        ''' Consigue un Authenticator Service '''
        self._auth_prx_ = self._main_prx_.getAuthenticator()

    # Actualizado
    def getTile(self, mediaId: str, userToken: str, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Retorna un objeto Media con la informacion del medio con el ID dado '''

        # Buscar el ID en temporal y temporal
        if mediaId not in self._media_.keys():
            raise IceFlix.WrongMediaId(mediaId)

        # Buscar en medios temporales
        media = self._media_.get(mediaId)
        if media:
            provider = self._media_.get(mediaId).provider
            if provider:
                try:
                    provider_prx = self._broker.stringToProxy(str(provider))
                    provider_prx.ice_ping()
                except Ice.ConnectionRefusedException:
                    raise IceFlix.TemporaryUnavailable
            else:

                raise IceFlix.TemporaryUnavailable

        self.update_main()
        try:
            self.update_auth()
        except IceFlix.TemporaryUnavailable:
            pass

        if not self._auth_prx_.isAuthorized(userToken):
            raise IceFlix.Unauthorized

        return self._media_.get(mediaId)


    def getTilesByName(self, name: str, exact: bool, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Devuelve una lista de IDs a partir del nombre dado'''

        id_list = []
        if exact:
            for media in self._media_.values():
                new_name = path.split(media.info.name)[1].lower()
                if name.lower().split(".")[0] == new_name.split(".")[0]:
                    id_list.append(media.mediaId)
        else:
            for media in self._media_.values():
                new_name = path.split(media.info.name)[1].lower()
                print(new_name)
                if name.lower().split(".")[0] in new_name.split(".")[0]:
                    id_list.append(media.mediaId)

        return id_list

    # Actualizado
    def getTilesByTags(self, tags: list, includeAllTags: bool, userToken, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Retorna una lista de IDs de los medios con las tags dadas '''
        self.update_main()
        try:
            self.update_auth()
        except IceFlix.TemporaryUnavailable:
            pass

        username = self._auth_prx_.whois(userToken)
        id_list = []
        media_tags = {}

        # Buscar al usuario en la bbdd para ver en qué medios tiene tags
        conn = sqlite3.connect(DB_PATH)
        ddbb_cursor = conn.cursor()
        ddbb_cursor.execute(f"SELECT media_id, tags from media where username='{username}'")
        query = ddbb_cursor.fetchall()
        conn.close()
        print(f"[TEST CATALOGO] Query con tags = {query}, con user {username}")
        if query:
            for entry in query:
                media_tags.update({entry[0]: entry[1].split(",")}) # MediaID: Tags

        print(media_tags)
        # Buscar si los tags son todos o no
        if includeAllTags:
            for key, value in media_tags.items():
                tags.sort()
                value.sort()
                if tags == value:
                    id_list.append(key)

        else:
            for key, value in media_tags.items():
                for tag in tags:
                    if tag in value:
                        id_list.append(key)
                        break
        print(id_list)
        return id_list

    def addTags(self, mediaId: str, tags: list, userToken, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Añade las tags dadas al medio con el ID dado '''

        self.update_main()
        try:
            self.update_auth()
        except IceFlix.TemporaryUnavailable:
            pass

        username = self._auth_prx_.whois(userToken)

        if mediaId not in self._media_:
            raise IceFlix.WrongMediaId(mediaId)

        self.add_tags(mediaId, tags, username)
        self._updates_sender.addTags(mediaId, tags, username)

    def removeTags(self, mediaId: str, tags: list, userToken, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Elimina las tags dadas del medio con el ID dado '''

        self.update_main()
        try:
            self.update_auth()
        except IceFlix.TemporaryUnavailable:
            pass

        username = self._auth_prx_.whois(userToken)

        if mediaId not in self._media_:
            raise IceFlix.WrongMediaId(mediaId)

        self.remove_tags(mediaId, tags, username)
        self._updates_sender.removeTags(mediaId, tags, username)

    def renameTile(self, mediaId, name, adminToken, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Renombra el medio de la estructura correspondiente '''

        self.update_main()
        if not self._main_prx_.isAdmin(adminToken):
            raise IceFlix.Unauthorized

        self.rename_tile(mediaId, name)
        self._updates_sender.renameTile(mediaId, name)


    def updateMedia(self, mediaId, initialName, provider, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Añade o actualiza el medio del ID dado '''

        info = IceFlix.MediaInfo(initialName, [])
        nuevo = IceFlix.Media(mediaId, provider, info)
        self._media_.update({mediaId: nuevo})


    @property
    def get_mediaDB(self):
        """ Devuelve un objeto MediaDB """

        medias = self._media_.items()

        mediaDBList = []

        for media_id, media_object in self._media_.items():
            media_info = media_object.info
            media_name = media_info.name
            media_tags = self.get_users_tags(media_id)
            mediaDBList.append(MediaDB(media_id, media_name, media_tags))

        # for media in medias:
        #     media_id, mediaO = media
        #     media_info = mediaO.info
        #     media_name = media_info.name
        #     media_tags = self.get_users_tags(media)
        #     mediaDBList.append(MediaDB(media_id, media_name, media_tags))

        return mediaDBList

    def is_in_catalog(self, mediaId):
        """ Permite saber si un media está en la bbdd """

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(f"SELECT * FROM media WHERE media_id LIKE '{mediaId}'") # pylint: disable=invalid-name,unused-argument

        query = c.fetchall()
        conn.close()
        # Buscar el ID en bbdd y temporal
        if not query:
            return False
        return True

    def add_tags(self, media_id, tags, user):   # HECHO
        ''' Añade las tags indicadas al usuario y medio correspondiente '''

        tags_string = self.list_to_string(tags)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(f"SELECT tags FROM media WHERE username='{user}' AND media_id='{media_id}'")
        result = c.fetchall()
        if result:
            current_tags = ""
            for tag in result[0]:
                current_tags += tag
                current_tags += ","
            tags_string += "," + current_tags[:-1]
            c.execute(f"""UPDATE media
                                SET tags='{tags_string}' 
                                WHERE media_id='{media_id}' AND username='{user}'""")
        else:
            c.execute(f"""INSERT INTO media
                      (media_id, username, tags) VALUES ('{media_id}', '{user}', '{tags_string}')
                      """)
        conn.commit()
        conn.close()
        print(f"[CATALOG] ID: {self.service_id} actualizadas tags de {media_id},  usuario {user}")


    def remove_tags(self, media_id, tags, user): # HECHO
        ''' Elimina las tags indicadas del usuario y medio correpondiente '''

        # Obtener las tags del usuario : Restar las tags que nos dicen : Updatear tags

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(f"SELECT tags FROM media WHERE username='{user}' AND media_id='{media_id}'")
        result = c.fetchall()

        if result:
            existing_tags = result[0][0]
            existing_tags = existing_tags.split(",")
            for tag in tags:
                if tag in existing_tags:
                    existing_tags.remove(tag)

            tags_string = self.list_to_string(existing_tags)
            c.execute(f"""UPDATE media
                                SET tags='{tags_string}' 
                                WHERE media_id='{media_id}' AND username='{user}'""")
            conn.commit()
        conn.close()

    def list_to_string(self, string_list):
        """ Permite crear una string juntando valores de una lista """

        tags_string = ""
        for i in range(len(string_list)):
            tags_string += string_list[i]
            if i != len(string_list)-1:
                tags_string += ","
        return tags_string

    def rename_tile(self, media_id, name): # Actualizado
        ''' Renombra el medio con el identificador dado al nuevo nombre '''

        # Buscar id en medios estáticos
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(f"SELECT * FROM media where media_id LIKE '{media_id}'")
        media = conn.commit()

        # Buscar id en medios dinamicos
        if media_id not in self._media_ and not media:
            raise IceFlix.WrongMediaId(media_id)

        # Cambiar media en medios dinamicos
        if media_id in self._media_:
            media = self._media_.get(media_id)
            old_name = media.info.name
            suffix = media.info.name.split(".")[1]
            resources = media.info.name.split("/")
            preffix = resources[0] + "/" + resources[1] + "/"
            media.info.name = preffix + name + "." + suffix
            self._media_.update({media_id: media})
            print(f"[MEDIA] Archivo {old_name} cambiado a {media.info.name}")

        # Cambiar en directorio
        if self.findfile(old_name):
            rename(old_name, RESOURCES_FOLDER + name + "." + suffix)

        # Actualizar en bbdd
        c = conn.cursor()
        c.execute(
            f"UPDATE media SET media_name = '{media.info.name}' WHERE media_id LIKE '{media_id}'")
        conn.commit()
        conn.close()

    def rename_dynamic_media(self, media_id, name):
        """ Actualiza el nombre de un medio en la lista dinámica """

        if media_id in self._media_:
            media = self._media_.get(media_id)
            suffix = media.info.name.split(".")[1]
            media.info.name = name + "." + suffix
            self._media_.update({media_id: media})


    def findfile(self, name):
        """ Encuentra el archivo en el directorio correspondiente """

        for file in glob.glob(RESOURCES_FOLDER + "*"):
            if file == name:
                return True
        return False

    def share_data_with(self, service, current=None): # pylint: disable=unused-argument
        """Share the current database with an incoming service."""

        service.updateDB(self.get_mediaDB, self.service_id)


    def updateDB(self, values, service_id, current=None):  # pylint: disable=invalid-name,unused-argument
        """Receives the current main service database from a peer."""

        print(f"Receiving remote data base from {service_id} to {self.service_id}")
        if service_id not in self._anunciamientos_listener.catalogs:
            raise IceFlix.UnknownService

        for media in values:
            print("Se recibe el objeto:")
            print(media)
            info = IceFlix.MediaInfo(media.name, media.tagsPerUser.values())
            self._media_.update({media.mediaId: IceFlix.Media(media.mediaId, None, info)})

    def update_main_prx(self):
        """ Busca un Main válido """

        for main_id in self._anunciamientos_listener.mains:
            main_prx = self._anunciamientos_listener.mains.get(main_id)
            try:
                main_prx.ice_ping()
                self._main_prx_ = main_prx
                return
            except IceFlix.TemporaryUnavailable:
                self._anunciamientos_listener.mains.pop(main_id)
        raise IceFlix.TemporaryUnavailable



class MediaCatalogServer(Ice.Application): # pylint: disable=too-many-instance-attributes
    ''' Servidor de Catálogo  '''

    def __init__(self):
        super().__init__()
        self.announcer = None
        self.subscriber = None
        self._updates_sender = None
        self._updates_listener = None
        self._stream_listener = None
        self.adapter = None
        self.proxy = None
        self.servant = None

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
        topic_manager = TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager")
        )

        try:
            topic = topic_manager.create(CATALOG_SYNC_TOPIC)
        except TopicExists:
            topic = topic_manager.retrieve(CATALOG_SYNC_TOPIC)

        self._updates_sender = CatalogUpdatesSender(
            topic, self.servant.service_id)

        self._updates_listener = CatalogUpdatesListener(
            self.servant, self.servant.service_id)

        subscriber_prx = self.adapter.addWithUUID(self._updates_listener)
        topic.subscribeAndGetPublisher({}, subscriber_prx)


    def setup_stream_announcements(self):
        '''  Configurar listener del topic StreamAnnouncements '''

        communicator = self.communicator()
        topic_manager = TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager")
        )
        try:
            topic = topic_manager.create(STREAM_ANNOUNCES_TOPIC)
        except TopicExists:
            topic = topic_manager.retrieve(STREAM_ANNOUNCES_TOPIC)

        self._stream_listener = StreamAnnouncementsListener(
            self.servant, self.servant.service_id, IceFlix.MediaCatalogPrx)

        subscriber_prx = self.adapter.addWithUUID(self._stream_listener)
        topic.subscribeAndGetPublisher({}, subscriber_prx)


    def run(self, args):
        sleep(1)

        broker = self.communicator()
        self.servant = MediaCatalogI()

        self.adapter = broker.createObjectAdapterWithEndpoints('MediaCatalogAdapter', 'tcp')
        self.adapter.add(self.servant, broker.stringToIdentity("MediaCatalog"))
        media_catalog_proxy = self.adapter.add(self.servant,
                                               Ice.stringToIdentity("MediaCatalogPrincipal"))

        self.proxy = media_catalog_proxy
        self.adapter.activate()

        self.setup_announcements()
        self.setup_catalog_updates()
        self.setup_stream_announcements()

        self.servant._anunciamientos_sender = self.announcer    #pylint: disable=protected-access
        self.servant._anunciamientos_listener = self.subscriber #pylint: disable=protected-access
        self.servant._updates_sender = self._updates_sender     #pylint: disable=protected-access
        self.servant._stream_listener = self._stream_listener   #pylint: disable=protected-access
        self.servant._broker = broker                           #pylint: disable=protected-access

        self.servant.read_media()
        self.announcer.start_service()

        print(f"[PROXY CATALOG] {self.proxy}")

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        self.announcer.stop()

if __name__ == '__main__':
    sys.exit(MediaCatalogServer().main(sys.argv))
