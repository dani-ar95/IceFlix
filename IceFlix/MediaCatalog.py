#!/usr/bin/python3

import sys, Ice
from IceFlix.MediaUploader import MediaUploaderI
Ice.loadSlice("iceflix.ice")
import IceFlix
import sqlite3


class MediaInfo(object):
    def __init__(self, name: str, tags: list):
        self.name = name
        self.tags = tags

class Media(object):
    def __init__(self, mediaID: str, provider, info: MediaInfo):
        self.mediaID = mediaID
        self.provider = provider
        self.info = info

class MediaCatalogI(IceFlix.MediaCatalog):

    def getTitle(self, mediaId: str, current=None):
        ''' Retorna un objeto Media con la informacion del medio con el ID dado '''
        
        if mediaId not in self._media_.keys():
            raise IceFlix.WrongID

        conn = sqlite3.connect("media.db")
        c = conn.cursor()
        c.execute("SELECT * FROM media WHERE id='{}'".format(mediaId))

        query = c.fetchall()

        provider = self._media_.get(mediaId)
        if not provider:
            raise IceFlix.TemporaryUnavailable

        id = query.pop(0)
        name = query.pop(0)
        tags = []
        while(query):
            tags.append(query.pop(0))

        info = MediaInfo(name, tags)
        media_obj = Media(mediaId, provider, info)
        conn.close()
        return media_obj

    def getTitlesByName(self, name, exact: bool, current=None):
        ''' Retorna una lista de IDs a partir del nombre dado'''

        conn = sqlite3.connect("media.db")
        c = conn.cursor()

        if exact:
            c.execute("SELECT id FROM media WHERE name='{}'".format(name))
        else: 
            c.execute("SELECT id FROM media WHERE LOWER(name) like LOWER('{}')".format(name))

        conn.close()
        id_list = c.fetchall()
        return id_list

    def getTitlesByTags(self, tags: list, includeAllTags: bool, userToken, current=None):
        ''' Retorna una lista de IDs de los medios con las tags dadas '''

        try:
            self.check_user(userToken)
        except IceFlix.Unauthorized as e, IceFlix.TemporaryUnavailable as p:
            raise IceFlix.Unauthorized
        else:

            conn = sqlite3.connect("media.db")
            c = conn.cursor()
            ids = []
            if includeAllTags:
                ids = c.execute("SELECT id FROM media WHERE tags = {}".format(tags))
            else:
                ids = c.execute("SELECT id FROM media WHERE tags IN {}".format(tags))

            conn.close()
            return ids


    def addTags(self, mediaId: str, tags: list, userToken, current=None):
        ''' Añade las tags dadas al medio con el ID dado '''

        try:
            self.check_user(userToken)
        except IceFlix.Unauthorized as e, IceFlix.TemporaryUnavailable as p:
            raise IceFlix.Unauthorized
        else:

            if mediaId not in self._media_.keys():
                raise IceFlix.WrongID 

            conn = sqlite3.connect("media.db")
            c = conn.cursor()

            current_tags = c.execute("SELECT tags FROM media WHERE id = ''".format(id))
            c.execute("UPDATE media SET tags = '{}' WHERE id = '{}'".format(tags.append(current_tags), mediaId))
            conn.commit()
            c.close()


    def removeTags(self, mediaId: str, tags: list,  userToken, current=None):
        ''' Elimina las tags dadas del medio con el ID dado '''

        try:
            self.check_admin(userToken)
        except IceFlix.Unauthorized as e, IceFlix.TemporaryUnavailable as p:
            raise IceFlix.Unauthorized
        else:        

            if mediaId not in self._media_.keys():
                raise IceFlix.WrongID

            conn = sqlite3.connect("media.db")
            c = conn.cursor()

            current_tags = c.execute("SELECT tags FROM media WHERE id = ''".format(id))
            new_tags = [x for x in current_tags if x not in tags]
            c.execute("UPDATE media SET tags = '{}' WHERE id = '{}'".format(tags.append(new_tags), mediaId))
            conn.commit()
            c.close()

    def renameTitle(self, id, name, adminToken, current=None):
        ''' Renombra el medio de la estructura correspondiente '''

        try:
            self.check_admin(adminToken)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized

        if id not in self._media_.keys():
            raise IceFlix.WrongMediaID

        else:
            media = self._media_.get(id)
            media.info.name = name
            self._media_.update(id, media)

    def updateMedia(self, id, initialName, provider, current=None):
        ''' Añade o actualiza el medio del ID dado '''

        info = MediaInfo(initialName, "tag")
        nuevo = Media(id, provider, info)
        self._media_.update({id: nuevo})

    def check_admin(self, admin_token: str):
        ''' Comprueba si un token es Administrador '''

        try:
            auth_prx = MediaCatalogServer.main_connection.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            raise IceFlix.TemporaryUnavailable
        else:
            if auth_prx.isAdmin(admin_token):
                return True
            else:
                raise IceFlix.Unauthorized

    def check_user(self, user_token: str):
        ''' Comprueba que la sesion del usuario es la actual '''

        try:
            auth_prx = MediaCatalogServer.main_connection.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            raise IceFlix.TemporaryUnavailable
        else:
            try:
                user = auth_prx.isAuthorized(user_token)
            except IceFlix.Unauthorized as e:
                raise e

    def __init__(self, current=None):
        self._media_ = dict()

class MediaCatalogServer(Ice.Application):
    def run(self, argv):
        #sleep(1)
        self.shutdownOnInterrupt()
        main_service_proxy = self.communicator().stringToProxy(argv[1])
        main_connection = IceFlix.MainPrx.checkedCast(main_service_proxy)
        if not main_connection:
            raise RuntimeError("Invalid proxy")

        broker = self.communicator()
        servant = MediaCatalogI()
        
        adapter = broker.createObjectAdapterWithEndpoints('MediaCatalogAdapter','tcp -p 9092')
        media_catalog_proxy = adapter.add(servant, broker.stringToIdentity('MediaCatalog'))
        
        adapter.activate()
        print(type(media_catalog_proxy))
        main_connection.register(media_catalog_proxy)
        
        self.shutdownOnInterrupt()
        broker.waitForShutdown()
        

sys.exit(MediaCatalogServer().main(sys.argv))