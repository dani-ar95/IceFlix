""" Modulo para manejar la comunicación entre instancias Authenticator """

from os import path
import uuid
import os
import Ice

try:
    import IceFlix
except ImportError:
    Ice.loadSlice(os.path.join(os.path.dirname(__file__), "iceflix.ice"))
    import IceFlix

auth_id = str(uuid.uuid4())

LOCAL_DB_PATH = path.join(path.join(path.dirname(__file__),
                       "persistence"), (auth_id + "_users.json"))

class UserUpdatesListener(IceFlix.UserUpdates):
    """ Listener del topic User updates """

    def __init__(self, own_servant, own_service_id, own_type):
        """ Inicialización del listener """

        self.servant = own_servant
        self.service_id = own_service_id
        self.own_type = own_type

        self.authenticators = {}
        self.catalogs = {}
        self.mains = {}
        self.known_ids = set()

    def newUser(self, user, passwordHash, srvId, current=None):
        """ Comportamiento al recibir un mensaje newUser """

        if srvId is not self.service_id:
            a = (user, passwordHash)
            self.servant.add_local_user(a, None)

    def newToken(self, user, userToken, srvId, current=None):
        """ Comportamiento al recibir un mensaje newToken """

        if srvId is not self.service_id:
            self.servant.add_token(user, userToken)  

class UserUpdatesSender:
    """ Sender del topic User updates """

    def __init__(self, topic, service_id, servant_proxy):
        """ Inicialización del sender """

        self.publisher = IceFlix.UserUpdatesPrx.uncheckedCast(
            topic.getPublisher()
        )
        self.service_id = service_id
        self.proxy = servant_proxy

    def newUser(self, user, passwordHash, current=None):
        self.publisher.newUser(user, passwordHash, self.service_id)

    def newToken(self, user, userToken, current=None):
        self.publisher.newToken(user, userToken, self.service_id)
