""" Modulo para manejar la comunicación entre instancias Authenticator """

import logging
import os
import threading
import Ice

try:
    import IceFlix
except ImportError:
    Ice.loadSlice(os.path.join(os.path.dirname(__file__), "iceflix.ice"))
    import IceFlix

class ServiceAnnouncementsListener(IceFlix.ServiceAnnouncements):
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
            self.servant.add_user(user, passwordHash)

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
        self.timer = None

    def newUser(self, user, passwordHash, srvId, current=None):
        self.publisher.newUser(user, passwordHash, srvId)

    def newToken(self, user, userToken, srvId, current=None):
        self.publisher.newToken(user, userToken, srvId)
