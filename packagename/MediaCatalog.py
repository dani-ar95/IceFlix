#!/usr/bin/python3

import sys, Ice
Ice.loadSlice("iceflix.ice")
import IceFlix
import sqlite3

class MediaCatalogI(IceFlix.MediaCatalog):

    def getTitle(self, id, current=None):
        # Código
        # Throws WrongMediaID, Temporaryunavailable
        # Retorna objeto tipo Media
        pass

    def getTitlesByName(self, name, exact: bool, current=None):
        # Código
        # Retorna objeto tipo StringList
        pass

    def getTitlesByTags(self, tags, includeAllTags: bool, userToken, current=None):
        # Código
        # Throws Unauthorized, WrongMediaID
        # Retorna objeto tipo StringList
        pass

    def addTags(self, id, tags, userToken, current=None):
        # Código
        # Throws Unauthorized, WrongMediaID
        pass

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
    
        main_connection.register(media_catalog_proxy)
        
        self.shutdownOnInterrupt()
        broker.waitForShutdown()
        

sys.exit(MediaCatalogServer().main(sys.argv))