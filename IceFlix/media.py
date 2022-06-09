import Ice # pylint: disable=import-error,wrong-import-position
from os import path

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")
Ice.loadSlice(SLICE_PATH)
import IceFlix # pylint: disable=import-error,wrong-import-position

class MediaDB(IceFlix.MediaDB):
    
    def __init__(self, mediaId, name, tagsPerUser):
        self.mediaId = mediaId
        self.name = name
        self.tagsPerUser = tagsPerUser
