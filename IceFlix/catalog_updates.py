from os import path

import Ice

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")

Ice.loadSlice(SLICE_PATH)
import IceFlix

class CatalogUpdates(IceFlix.CatalogUpdates):
    
    def __init__(self, catalog_service):
        self.catalog_service = catalog_service   #servant
        pass
    
    def renameTiles(self, media_id, name, srv_id):
        if srv_id == self.catalog_service.id or not self.catalog_service.catalog.is_in_catalog(media_id):
            return
            
        self.catalog_service.renameTiles(media_id, name)
        pass
    
    def addTags(self, media_id, tags, user, srv_id):
        if srv_id == self.catalog_service.id:
            return
        '''
            TODO: Comprobar que el media_id existe en el catalogo(?)
                Mover comprobacion user y media_id aquí(?)
        '''
        self.catalog_service.addTags(media_id, tags)
        pass
        
    def removeTags(self, media_id, tags, user, srv_id):
        if srv_id == self.catalog_service.id:
            return
        '''
            TODO: Comprobar que el media_id existe en el catalogo(?)
                Mover comprobacion user y media_id aquí(?)
        '''
        self.catalog_service.removeTags(media_id, tags)
        pass