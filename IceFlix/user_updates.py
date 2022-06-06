""" Modulo para manejar información de usuarios """

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
    """Listener for the ServiceAnnouncements topic."""

    def __init__(self, own_servant, own_service_id, own_type):
        """ Initialize a ServiceAnnouncements topic listener """

        self.servant = own_servant
        self.service_id = own_service_id
        self.own_type = own_type

        self.authenticators = {}
        self.catalogs = {}
        self.mains = {}
        self.known_ids = set()

    def newUser(self, user, passwordHash, srvId, current=None):
        if srvId is not self.service_id:
            self.servant.add_user(user, passwordHash)

    def newToken(self, user, userToken, srvId, current=None):
        if srvId is not self.service_id:
            self.servant.add_token(user, userToken)  

class UserUpdatesSender:
    """ Permite enviar eventos al canal de manejar usuarios """

    def __init__(self, topic, service_id, servant_proxy):

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
