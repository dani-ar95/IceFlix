#!/usr/bin/python3
# pylint: disable=invalid-name
''' Servicio de Catálogo, se encarga de listar los medios disponibles, persistentes
    y los anunciados por los Providers '''

import sqlite3
import sys
import json
from time import sleep
from os import path, rename
import Ice

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")
DB_PATH = path.join(path.dirname(__file__), "media.db")
USERS_PATH = path.join(path.dirname(__file__), "users.json")
Ice.loadSlice(SLICE_PATH)
import IceFlix # pylint: disable=wrong-import-position

class MediaCatalogI(IceFlix.MediaCatalog): # pylint: disable=inherit-non-class
    ''' Instancia del servicio de Catálogo '''

    def __init__(self):
        self._media_ = {}
        self._main_prx_ = None
        self._auth_prx_ = None

        conn = sqlite3.connect(DB_PATH)
        ddbb_cursor = conn.cursor()
        ddbb_cursor.execute("SELECT * FROM media")
        query = ddbb_cursor.fetchall()
        conn.close()
        if query:
            for media in query:
                info = IceFlix.MediaInfo(media[1], [])
                self._media_.update({media[0]: IceFlix.Media(media[0], None, info)})


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

        else:
            if mediaId not in self._media_:
                raise IceFlix.WrongMediaId

            # Cambiar tags persistentes
            with open(USERS_PATH, "r", encoding="utf8") as file_descriptor:
                obj = json.load(file_descriptor)

            for i in obj["users"]:
                if i["user"] == user_name:
                    actuales = i["tags"].get(mediaId)
                    if not actuales:
                        actuales = []
                    for tag in tags:
                        actuales.append(tag)
                    i["tags"].update({mediaId:actuales})
                    break

            with open(USERS_PATH, 'w', encoding="utf8") as file:
                json.dump(obj, file, indent=2)


    def removeTags(self, mediaId: str, tags: list, userToken, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Elimina las tags dadas del medio con el ID dado '''

        try:
            user_name = self.check_user_name(userToken)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized
        else:

            # Cambiar tags persistentes
            with open(USERS_PATH, "r", encoding="utf8") as f:
                obj = json.load(f)

            for i in obj["users"]:
                if i["user"] == user_name:
                    actuales = i["tags"].get(mediaId)
                    for tag in tags:
                        if tag in actuales:
                            actuales.remove(tag)
                    i["tags"].update({mediaId:actuales})
                    break

            with open(USERS_PATH, 'w', encoding="utf8") as file:
                json.dump(obj, file, indent=2)


    def renameTile(self, mediaId, name, adminToken, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Renombra el medio de la estructura correspondiente '''

        try:
            self.check_admin(adminToken)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized
        else:

            # Buscar id en medios estáticos
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(f"SELECT * FROM media where id LIKE '{mediaId}'")
            media = conn.commit()
            conn.close()

            # Buscar id en medios dinamicos
            if mediaId not in self._media_ and not media:
                raise IceFlix.WrongMediaId

            # Cambiar media en medios dinamicos
            if mediaId in self._media_:
                media = self._media_.get(mediaId)
                old_name = media.info.name
                suffix = media.info.name.split(".")[1]
                media.info.name = name + "." + suffix
                self._media_.update({mediaId: media})

            # Cambiar en directorio
            try:
                rename(old_name, "IceFlix/resources/" + name + "." + suffix)
            except FileNotFoundError:
                raise IceFlix.WrongMediaId

            # Buscar medio en bbdd
            try:
                in_ddbb = self.getTile(mediaId)
            except IceFlix.Unauthorized:
                raise IceFlix.Unauthorized

            else:
                if in_ddbb:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute(
                        f"UPDATE media SET name = '{name}.mp4' WHERE id LIKE '{mediaId}'")
                    conn.commit()
                    conn.close()


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

    def share_data_with(self, service):
        """Share the current database with an incoming service."""
        service.updateDB(None, self.service_id)

class MediaCatalogServer(Ice.Application):
    ''' Servidor de Catálogo  '''

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
            self.servant, self.servant.service_id, IceFlix.MediaCatalogPrx
        )

        subscriber_prx = self.adapter.addWithUUID(self.subscriber)
        topic.subscribeAndGetPublisher({}, subscriber_prx)

    def run(self, argv):
        sleep(2)
        main_service_proxy = self.communicator().stringToProxy(argv[1])
        main_connection = IceFlix.MainPrx.checkedCast(main_service_proxy)
        if not main_connection:
            raise RuntimeError("Invalid proxy")

        broker = self.communicator()
        servant = MediaCatalogI()

        adapter = broker.createObjectAdapterWithEndpoints(
            'MediaCatalogAdapter', 'tcp -p 9092')
        media_catalog_proxy = adapter.add(
            servant, broker.stringToIdentity('MediaCatalog'))

        adapter.activate()

        self.setup_announcements()
        self.announcer.start_service()

        main_connection.register(media_catalog_proxy)

        servant._main_prx_ = main_connection
        try:
            servant._auth_prx_ = main_connection.getAuthenticator()
        except IceFlix.TemporaryUnavailable as e:
            print(e)

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        self.announcer.stop()

if __name__ == '__main__':
    # MediaCatalogServer().run(sys.argv)
    sys.exit(MediaCatalogServer().main(sys.argv))
