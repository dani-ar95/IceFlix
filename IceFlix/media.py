import Ice # pylint: disable=import-error,wrong-import-position
from os import path

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")
Ice.loadSlice(SLICE_PATH)
import IceFlix # pylint: disable=import-error,wrong-import-position

class MediaDB(IceFlix.MediaDB):
    
    def __init__(self, media_id, name, tags_per_user):
        self.media_id = media_id
        self.name = name
        self.tags_per_user = tags_per_user
