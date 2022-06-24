''' Modulo para manejar la comunicación entre instancias MediaCatalog '''
import os

import Ice

try:
    import IceFlix
except ImportError:
    Ice.loadSlice(os.path.join(os.path.dirname(__file__), "iceflix.ice"))
    import IceFlix  #pylint: disable=wrong-import-position

class CatalogUpdatesListener(IceFlix.CatalogUpdates):
    """ Listener del topic CatalogUpdates """

    def __init__(self, catalog_service, own_service_id):
        """ Inicialización del listener """

        self.catalog_service = catalog_service
        self.service_id = own_service_id

    def renameTile(self, mediaId, name, srvId, current=None): # pylint: disable=invalid-name,unused-argument
        """ Comportamiento al recibir un mensaje renameTiles """

        if srvId == self.service_id or not self.catalog_service.is_in_catalog(mediaId):
            return

        self.catalog_service.renameTiles(mediaId, name)


    def addTags(self, mediaId, tags, user, srvId, current=None): # pylint: disable=invalid-name,unused-argument,too-many-arguments
        """ Comportamiento al recibir un mensaje addTags """

        if srvId == self.service_id or not self.catalog_service.is_in_catalog(mediaId):
            return

        self.catalog_service.add_tags(mediaId, tags, user)


    def removeTags(self, mediaId, tags, user, srvId, current=None): # pylint: disable=invalid-name,unused-argument,too-many-arguments
        """ Comportamiento al recibir un mensaje removeTags """

        if srvId == self.service_id or not self.catalog_service.is_in_catalog(mediaId):
            return

        self.catalog_service.removeTags(mediaId, tags, user)


class CatalogUpdatesSender():
    ''' Sender del topic Catalog Updates '''

    def __init__(self, topic, service_id):
        """ Inicialización del sender """

        self.publisher = IceFlix.CatalogUpdatesPrx.uncheckedCast(
            topic.getPublisher()
        )
        self.service_id = service_id

    def renameTile(self, mediaId, name):  # pylint: disable=invalid-name,unused-argument
        ''' Envía un mensaje renameTile'''
        self.publisher.renameTile(mediaId, name, self.service_id)

    def addTags(self, mediaId, tags, user):  # pylint: disable=invalid-name,unused-argument
        '''Envía un mensaje addTags'''
        self.publisher.addTags(mediaId, tags, user, self.service_id)

    def removeTags(self, mediaId, tags, user):  # pylint: disable=invalid-name,unused-argument
        '''Envía un mensaje removeTags'''
        self.publisher.removeTags(mediaId, tags, user, self.service_id)
