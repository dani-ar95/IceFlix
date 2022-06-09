""" Modulo para manejar la comunicación al eliminar usuarios o tokens """

import os
import Ice

try:
    import IceFlix
except ImportError:
    Ice.loadSlice(os.path.join(os.path.dirname(__file__), "iceflix.ice"))
    import IceFlix

class RevocationsListener(IceFlix.Revocations):
    """ Listener del topic Revocations"""

    def __init__(self, own_servant, own_service_id, own_type):
        """ Inicialización del listener """

        self.servant = own_servant
        self.service_id = own_service_id
        self.own_type = own_type

        self.authenticators = {}
        self.catalogs = {}
        self.mains = {}
        self.known_ids = set()

    def revokeToken(self, userToken, srvId, current=None):
        """ Comportamiento al recibir un mensaje revokeToken """

        if srvId is not self.service_id:
            self.servant.remove_token(userToken)


    def revokeUser(self, user, srvId, current=None):
        """ Comportamiento al recibir un mensaje revokeUser """

        if srvId is not self.service_id:
            self.servant.remove_user(user)


class RevocationsSender:
    """ Sender del topic Revocations """

    def __init__(self, topic, service_id, servant_proxy, current=None):
        """ Inicialización del sender """

        self.publisher = IceFlix.RevocationsPrx.uncheckedCast(
            topic.getPublisher()
        )
        self.service_id = service_id
        self.proxy = servant_proxy
        self.timer = None

    def revokeUser(self, user, current=None):
        self.publisher.revokeUser(user, self.service_id)

    def revokeToken(self, userToken, current=None):
        self.publisher.revokeToken(userToken, userToken, self.service_id)
