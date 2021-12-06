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
        # Comprobar ID -> WrongMediaID

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

        # Comprobar WrongMediaID
        try:
            self.check_user(userToken)
        except IceFlix.Unauthorized e, IceFlix.TemporaryUnavailable p:
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


    def addTags(self, id: str, tags: list, userToken, current=None):
        # Código
        try:
            self.check_user(userToken)
        except IceFlix.Unauthorized e, IceFlix.TemporaryUnavailable p:
            raise IceFlix.Unauthorized
        else:
            # Comprobar id
            conn = sqlite3.connect("media.db")
            c = conn.cursor()

            c.execute("UPDATE media SET tags  ")
        # Throws  WrongMediaID
        # Comprobar MediaID




    def removeTags(self, id, name, adminToken, current=None):
        # Código
        # Throws Unauthorized, WrongMediaID
        pass

    def renameTitle(self, id, name, adminToken, current=None):
        # Cödigo
        # Throws Unauthorized, WrongMediaID
        pass

    def updateMedia(self, id, initialName, provider):
        # Código
        # Throws Unauthorized, WrongMediaID
        pass

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
        try:
            auth_prx = MediaCatalogServer.main_connection.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            raise IceFlix.TemporaryUnavailable
        else:
            try:
                user = auth_prx.isAuthorized(user_token)
            except IceFlix.Unauthorized e:
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