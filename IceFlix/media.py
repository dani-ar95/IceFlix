''' Modulo para la implementación de la bbdd de los medios '''

import os
import Ice

try:
    import IceFlix
except ImportError:
    Ice.loadSlice(os.path.join(os.path.dirname(__file__), "iceflix.ice"))
    import IceFlix # pylint: disable=import-error,wrong-import-position

class MediaDB(IceFlix.MediaDB): #pylint: disable=too-few-public-methods
    ''' Clase para el objeto MediaDB '''

    def __init__(self, mediaId, name, tagsPerUser): # pylint: disable=invalid-name
        self.mediaId = mediaId # pylint: disable=invalid-name
        self.name = name
        self.tagsPerUser = tagsPerUser # pylint: disable=invalid-name
