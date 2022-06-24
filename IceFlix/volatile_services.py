''' Módulo para la implementación de la clase que almacena
los servicios volátiles '''

import os
import Ice # pylint: disable=import-error,wrong-import-position

try:
    import IceFlix
except ImportError:
    Ice.loadSlice(os.path.join(os.path.dirname(__file__), "iceflix.ice"))
    import IceFlix # pylint: disable=import-error,wrong-import-position

class VolatileServices(IceFlix.VolatileServices):
    ''' Clase para el objeto VolatileServices '''

    def __init__(self,
                 auth_services, catalog_services, current=None): # pylint: disable=unused-argument
        self.authenticators = auth_services
        self.mediaCatalogs = catalog_services # pylint: disable=invalid-name

    def get_authenticators(self):
        ''' Retorna la lista de Authenticators '''
        return self.authenticators

    def get_catalogs(self):
        ''' Retorna la lista de MediaCatalogs'''
        return self.mediaCatalogs
