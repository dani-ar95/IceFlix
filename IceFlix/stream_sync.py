import threading
import Ice # pylint: disable=import-error,wrong-import-position
import os

try:
    import IceFlix
except ImportError:
    Ice.loadSlice(os.path.join(os.path.dirname(__file__), "iceflix.ice"))
    import IceFlix # pylint: disable=import-error,wrong-import-position
    
class StreamSyncListener(IceFlix.StreamSync):
    
    def __init__(self, own_servant):
        self.servant = own_servant
    
    def requestAuthentication(self, current=None):
        self.servant.authentication_timer = threading.Timer(5.0, self.servant.stop)
        self.servant.authentication_timer.start()
        
class StreamSyncSender:
    def __init__(self, topic):
        self.publisher = IceFlix.StreamSyncPrx.uncheckedCast(topic.getPublisher())
        
    def requestAuthentication(self):
        self.publisher.reqestAuthentication()