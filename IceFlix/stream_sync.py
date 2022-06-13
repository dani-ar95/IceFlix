import Ice # pylint: disable=import-error,wrong-import-position
import os

try:
    import IceFlix
except ImportError:
    Ice.loadSlice(os.path.join(os.path.dirname(__file__), "iceflix.ice"))
    import IceFlix # pylint: disable=import-error,wrong-import-position
    
class StreamSync(IceFlix.StreamSync):
    
    def __init__(self):
        pass
    
    def requestAuthentication(self):
        pass