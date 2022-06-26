#!/usr/bin/python3
# pylint: disable=invalid-name
''' Servicio de Catálogo, se encarga de listar los medios disponibles, persistentes
    y los anunciados por los Providers '''

import sqlite3
import sys
import json
from time import sleep
from os import path, rename
import glob
import IceStorm
import uuid
import random
from stream_announcements import StreamAnnouncementsListener
from service_announcement import ServiceAnnouncementsListener, ServiceAnnouncementsSender
from catalog_updates import CatalogUpdatesListener, CatalogUpdatesSender
import Ice
SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")
DB_PATH = path.join(path.dirname(__file__), "media.db")
USERS_PATH = "IceFlix/users.json"
RESOURCES_FOLDER = path.join(path.dirname(__file__), "resources/")
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
        
    
    def read_media(self): # Actualizado
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
        if self.is_in_catalog(media_id):
            self._media_.pop(media_id)
        return


    def find_provider(self, srv_id):
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

        for info in query:
            users_tags.update(info[0], info[1].split(","))

        return users_tags

    # Actualizado
    def getTile(self, mediaId: str, userToken: str, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Retorna un objeto Media con la informacion del medio con el ID dado '''

        if not self.check_user(userToken): # También puede lanzar TemporaryUnavailable -> Está bien
            raise IceFlix.Unauthorized
        
        # Buscar en medios temporales
        media = self._media_.get(mediaId)
        print(media)
        if media:
            provider = self._media_.get(mediaId).provider
            if provider:
                try:
                    provider.ice_ping()
                except Ice.ConnectionRefusedException:
                    raise IceFlix.TemporaryUnavailable
                else:
                    return self._media_.get(mediaId)
            else:
                raise IceFlix.TemporaryUnavailable

        # # Si no lo encuentra en los medios locales: Buscar ID en bbdd
        # conn = sqlite3.connect(DB_PATH)
        # c = conn.cursor()
        # c.execute(f"SELECT * FROM media WHERE media_id LIKE '{mediaId}'") # pylint: disable=invalid-name,unused-argument
        # query = c.fetchall()

        # Buscar el ID en bbdd y temporal
        if mediaId not in self._media_.keys():
            raise IceFlix.WrongMediaId(mediaId)


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

        try:
            username = self.check_user_name(userToken) # Raisea TemporaryUnavailable, Unauthorized
        except IceFlix.TemporaryUnavailable: # La intefaz no permite raisear esto -> Se cambia por otra que se pueda
            raise IceFlix.Unauthorized

        id_list = []
        media_tags = {}

        # Buscar al usuario en la bbdd para ver en qué medios tiene tags
        conn = sqlite3.connect(DB_PATH)
        ddbb_cursor = conn.cursor()
        ddbb_cursor.execute(f"SELECT media_id, tags from media where username='{username}'")
        query = ddbb_cursor.fetchall()
        conn.close()
        if query:
            for entry in query:
                media_tags.update({entry[0]: entry[1].split(",")}) # MediaID: Tags

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

        try:
            user_name = self.check_user_name(userToken) # Raisea TemporaryUnavailable, Unauthorized
        except IceFlix.TemporaryUnavailable: # No se puede raisear esta, se cambia por otra
            raise IceFlix.Unauthorized

        if mediaId not in self._media_:
            raise IceFlix.WrongMediaId(mediaId)

        self.add_tags(mediaId, tags, user_name)
        self._updates_sender.addTags(mediaId, tags, user_name)

    def removeTags(self, mediaId: str, tags: list, userToken, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Elimina las tags dadas del medio con el ID dado '''

        try:
            user_name = self.check_user_name(userToken) # Raisea TemporaryUnavailable, Unauthorized
        except IceFlix.TemporaryUnavailable: # No se puede raisear esta, se cambia por otra
            raise IceFlix.Unauthorized
        
        if mediaId not in self._media_:
            raise IceFlix.WrongMediaId(mediaId)

        self.remove_tags(mediaId, tags, user_name)
        self._updates_sender.removeTags(mediaId, tags, user_name)

    def renameTile(self, mediaId, name, adminToken, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Renombra el medio de la estructura correspondiente '''

        try:
            self.update_main_prx() # Puede lanzar TemporaryUnavailable, pero la interfaz no deja
        except IceFlix.TemporaryUnavailable:
            raise IceFlix.Unauthorized

        self.check_admin(adminToken) # Puede lanzar Unauthorized
        self.rename_tile(mediaId, name)
        self._updates_sender.renameTile(mediaId, name)


    def updateMedia(self, mediaId, initialName, provider, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Añade o actualiza el medio del ID dado '''

        info = IceFlix.MediaInfo(initialName, [])
        nuevo = IceFlix.Media(mediaId, provider, info)
        self._media_.update({mediaId: nuevo})


    def check_admin(self, admin_token: str):
        ''' Comprueba si un token es Administrador '''

        main_prx = random.choice(list(self._anunciamientos_listener.mains.values()))
        try:
            is_admin = main_prx.isAdmin(admin_token)
            if not is_admin:
                raise IceFlix.Unauthorized
        except IceFlix.TemporaryUnavailable:
            raise IceFlix.Unauthorized
        else:
            return is_admin


    def check_user(self, user_token: str):
        ''' Comprueba que la sesion del usuario es la actual '''

        self.update_auth()
        return self._auth_prx_.isAuthorized(user_token)

    def check_user_name(self, user_token: str):
        ''' Devuelve el usuario al que pertenece el token dado '''
        
        self.update_auth() # Raisea TemporaryUnavailable
        user_name = self._auth_prx_.whois(user_token) # Raisea Unauthorized

        return user_name

    def update_auth(self):
        """ Actualiza el proxy al authenticator """

        while self._anunciamientos_listener.mains.values():
            main_prx = random.choice(list(self._anunciamientos_listener.mains.values())) # Cambiar por si cae
            try:
                main_prx.ice_ping()
                self._auth_prx_ = main_prx.getAuthenticator()
                self._main_prx_ = main_prx
                break
            except Ice.ConnectionRefusedException:
                self._anunciamientos_listener.mains.pop(main_prx) # Comprobar si funciona

        raise IceFlix.TemporaryUnavailable
    
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
                                SET tags='{tags_string}' WHERE media_id='{media_id}' AND username='{user}'""")
        else:
            c.execute(f"""INSERT INTO media 
                      (media_id, username, tags) VALUES ('{media_id}', '{user}', '{tags_string}')""")
        conn.commit()
        conn.close()
        print(f"[CATALOG] ID: {self.service_id} actualizadas tags de {media_id} para usuario {user}")


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
                                SET tags='{tags_string}' WHERE media_id='{media_id}' AND username='{user}'""")
            conn.commit()
        conn.close()

    def list_to_string(self, string_list):
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
            raise IceFlix.WrongMediaId

        # Cambiar media en medios dinamicos
        if media_id in self._media_:
            media = self._media_.get(media_id)
            old_name = media.info.name
            suffix = media.info.name.split(".")[1]
            media.info.name = name + "." + suffix
            self._media_.update({media_id: media})

        # Cambiar en directorio
        if self.findfile(old_name):
            try:
                rename(old_name, RESOURCES_FOLDER + media.info.name )
            except FileNotFoundError:
                raise IceFlix.WrongMediaId

        # Actualizar en bbdd
        c = conn.cursor()
        c.execute(
            f"UPDATE media SET media_name = '{media.info.name}' WHERE media_id LIKE '{media_id}'")
        conn.commit()
        conn.close()

    def rename_dynamic_media(self, media_id,  name):
        """ Actualiza el nombre de un medio en la lista dinámica """

        if media_id in self._media_:
            media = self._media_.get(media_id)
            suffix = media.info.name.split(".")[1]
            media.info.name = name + "." + suffix
            self._media_.update({media_id: media})


    def findfile(self, name):
        for file in glob.glob(RESOURCES_FOLDER + "*"):
            if file == name:
                return True
        return False

    def share_data_with(self, service, current=None):
        """Share the current database with an incoming service."""
        service.updateDB(self.get_mediaDB, self.service_id)


    def updateDB(self, values, service_id, current=None):  # pylint: disable=invalid-name,unused-argument
        """Receives the current main service database from a peer."""
        print(f"Receiving remote data base from {service_id} to {self.service_id}")
        
        for media in values:
            print("Se recibe el objeto:")
            print(media)
            info = IceFlix.MediaInfo(media.name, media.tagsPerUser.values())
            self._media_.update({media.mediaId: IceFlix.Media(media.mediaId, None, info)})

    def update_auth(self):
        # Update main
        self.update_main_prx()
        # Comprobar Main funcionando
        try:
            self._main_prx_.ice_ping()
        except Ice.ConnectionRefusedException:
            raise IceFlix.TemporaryUnavailable

        # Volver a pedir authenticator
        try:
            self._auth_prx_ = self._main_prx_.getAuthenticator()
            self._auth_prx_.ice_ping()
        except IceFlix.TemporaryUnavailable or AttributeError: # Authenticator caido o no existe
            raise IceFlix.TemporaryUnavailable

    def update_main_prx(self):
        for main_id in self._anunciamientos_listener.mains:
            main_prx = self._anunciamientos_listener.mains.get(main_id)
            try:
                main_prx.ice_ping()
                self._main_prx_ = main_prx
                return
            except IceFlix.TemporaryUnavailable:
                self._anunciamientos_listener.mains.pop(main_id)
        raise IceFlix.TemporaryUnavailable



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

        self._updates_sender = CatalogUpdatesSender(
            topic, self.servant.service_id)

        self._updates_listener = CatalogUpdatesListener(
            self.servant, self.servant.service_id)

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
        self.adapter.add(self.servant, broker.stringToIdentity("MediaCatalog"))
        media_catalog_proxy = self.adapter.add(self.servant, Ice.stringToIdentity("MediaCatalogPrincipal"))

        self.proxy = media_catalog_proxy
        self.adapter.activate()

        self.setup_announcements()
        self.setup_catalog_updates()
        self.setup_stream_announcements()

        self.servant._anunciamientos_sender = self.announcer
        self.servant._anunciamientos_listener = self.subscriber
        self.servant._updates_sender = self._updates_sender
        self.servant._stream_listener = self._stream_listener

        self.servant.read_media()
        self.announcer.start_service()

        print(f"[PROXY CATALOG] {self.proxy}")

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        self.announcer.stop()

if __name__ == '__main__':
    sys.exit(MediaCatalogServer().main(sys.argv))
