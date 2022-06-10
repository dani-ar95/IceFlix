from os import path

import Ice

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")

Ice.loadSlice(SLICE_PATH)
import IceFlix

class CatalogUpdatesListener(IceFlix.CatalogUpdates):
    
    def __init__(self, catalog_service):
        self.catalog_service = catalog_service   #servant

    
    def renameTiles(self, mediaId, name, srvId, current=None):
        if srvId == self.catalog_service.id or not self.catalog_service.is_in_catalog(mediaId):
            return
            
        self.catalog_service.renameTiles(mediaId, name)

    
    def addTags(self, mediaId, tags, user, srvId, current=None):
        if srvId == self.catalog_service.id:
            return
        '''
            TODO: Comprobar que el media_id existe en el catalogo(?)
                Mover comprobacion user y media_id aquí(?)

            ¿Puede ser que no haga falta?
        '''
        self.catalog_service.add_tags(mediaId, tags, user)

        
    def removeTags(self, mediaId, tags, user, srvId, current=None):
        if srvId == self.catalog_service.id:
            return
        '''
            TODO: Comprobar que el media_id existe en el catalogo(?)
                Mover comprobacion user y media_id aquí(?)
        '''
        self.catalog_service.removeTags(mediaId, tags, user)


class CatalogUpdatesSender():
    ''' Sender del topic Catalog Updates '''

    def __init__(self, topic, service_id, servant_proxy):
        """ Inicialización del sender """

        self.publisher = IceFlix.CatalogUpdatesPrx.uncheckedCast(
            topic.getPublisher()
        )
        self.service_id = service_id
        self.proxy = servant_proxy

    def renameTiles(self, mediaId, name, current=None):
        self.publisher.renameTiles(mediaId, name, self.service_id)

    def addTags(self, mediaId, tags, user, current=None):
        self.publisher.addTags(mediaId, tags, user, self.service_id)

    def removeTags(self, mediaId, tags, user, current=None):
        self.publisher.removeTags(mediaId, tags, user, self.service_id)