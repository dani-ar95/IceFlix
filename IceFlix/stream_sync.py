'''Modulo para manejar la sincronización de streaming
entre cliente y StreamController'''

import threading
import os
import Ice

try:
    import IceFlix
except ImportError:
    Ice.loadSlice(os.path.join(os.path.dirname(__file__), "iceflix.ice"))
    import IceFlix # pylint: disable=import-error,wrong-import-position

class StreamSyncListener(IceFlix.StreamSync): # pylint: disable=too-few-public-methods
    '''Listener del topic StreamSync'''

    def __init__(self, own_servant, own_proxy=None):
        self.servant = own_servant
        self.proxy = own_proxy

    def requestAuthentication(self, current=None): #pylint: disable=invalid-name,unused-argument
        ''' Comportamiento al recibir un mensaje requestAuthentication.
            Refresca el token del usuario '''
        if self.proxy:
            if self.proxy.ice_isA("::IceFlix::StreamController"):
                refreshing_timer = threading.Timer(1.0, self.servant.refreshAuthentication,
                                                [self.servant.user_token])
                refreshing_timer.start()

        else:
            if self.servant.refreshed_token:
                self.servant._stream_controller_prx_.refreshAuthentication(self.servant._user_token_) # pylint: disable=protected-access


class StreamSyncSender: # pylint: disable=too-few-public-methods
    '''Sender del topic StreamSync'''

    def __init__(self, topic):
        self.publisher = IceFlix.StreamSyncPrx.uncheckedCast(topic.getPublisher())

    def requestAuthentication(self): #pylint: disable=invalid-name
        ''' Envía un mensaje requestAuthentication '''

        self.publisher.requestAuthentication()
