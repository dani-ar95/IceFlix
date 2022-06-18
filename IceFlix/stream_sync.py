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
        if self.servant.refreshed_token:
            print("[CLIENT] Actualizando token")
            self.servant._stream_controller_prx_.refreshAuthentication(self.servant._user_token_)  
        else: 
            refreshing_timer = threading.Timer(1.0, self.servant.refreshAuthentication, 
                                               [self.servant.user_token])
            refreshing_timer.start()
            print("[CONTROLLER] Comprobando token")
        
class StreamSyncSender:
    def __init__(self, topic):
        self.publisher = IceFlix.StreamSyncPrx.uncheckedCast(topic.getPublisher())
        
    def requestAuthentication(self):
        self.publisher.requestAuthentication()