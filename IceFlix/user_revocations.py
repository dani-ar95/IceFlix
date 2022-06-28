""" Modulo para manejar la comunicación al eliminar usuarios o tokens """

import os
import threading
from time import sleep
import Ice
import logging
try:
    import IceFlix
except ImportError:
    Ice.loadSlice(os.path.join(os.path.dirname(__file__), "iceflix.ice"))
    import IceFlix

class RevocationsListener(IceFlix.Revocations):
    """ Listener del topic Revocations"""

    def __init__(self, own_servant, own_proxy=None, own_service_id=None, own_type=None): # pylint: disable=unused-argument
        """ Inicialización del listener """

        self.servant = own_servant
        self.service_id = own_service_id
        self.own_type = own_type
        self.service = own_proxy

    def revokeToken(self, userToken, srvId, current=None): # pylint: disable=invalid-name,unused-argument
        """ Comportamiento al recibir un mensaje revokeToken """
        if self.service is not None:

            if self.service.ice_isA("::IceFlix::Authenticator"):
                self.servant.remove_token(userToken)
                print("[AUTHENTICATOR] Token revoked")

            if self.service.ice_isA("::IceFlix::StreamController"):
                print("STREAM CONTROLLER REVOCATIONS")
                if srvId == self.service_id:
                    return
                print(self.servant.user_token, userToken)
                if self.servant.user_token == userToken:
                    print("\n\n[STREAM CONTROLLER] Token revoked. Refreshing...")
                    self.servant.stream_sync_announcer.requestAuthentication()
                    self.servant.authentication_timer = threading.Timer(5.0, self.servant.stop)
                    self.servant.authentication_timer.start()

        else:
            if self.servant.logged:
                self.servant.refreshed_token = False
                try:
                    auth = self.servant._main_prx_.getAuthenticator() # pylint: disable=protected-access
                    new_token = auth.refreshAuthorization(self.servant._username_, # pylint: disable=protected-access
                                                          self.servant._password_hash_) # pylint: disable=protected-access
                    self.servant._user_token_ = new_token # pylint: disable=protected-access
                    self.servant.refreshed_token = True
                    print("[REVOCATIONS] Token actualizao: ", new_token)
                except IceFlix.TemporaryUnavailable:
                    print("No se ha encontrado ningún servicio de Autenticación")
                    self.servant.logout()
                except IceFlix.Unauthorized:
                    print("Crendeciales no válidas")
                    self.servant.logout()

    def revokeUser(self, user, srvId, current=None): # pylint: disable=invalid-name,unused-argument
        """ Comportamiento al recibir un mensaje revokeUser """

        if self.service and self.service.ice_isA("::IceFlix::Authenticator"):
            if srvId == self.service_id:
                return

        self.servant.remove_local_user(user)


class RevocationsSender:
    """ Sender del topic Revocations """

    def __init__(self, topic, service_id=None, servant_proxy=None, current=None): # pylint: disable=unused-argument
        """ Inicialización del sender """

        self.publisher = IceFlix.RevocationsPrx.uncheckedCast(
            topic.getPublisher()
        )
        self.service_id = service_id
        self.proxy = servant_proxy

    def revokeUser(self, user, current=None): # pylint: disable=invalid-name,unused-argument
        """ Emite un evento revokeUser """

        print(f"[UserRevocations] (Emite revokeUser) ID: {self.service_id}, User: {user}.")
        self.publisher.revokeUser(user, self.service_id)

    def revokeToken(self, userToken, current=None): # pylint: disable=invalid-name,unused-argument
        """ Emite un evento revokeToken """

        print(f"[UserRevocations] (Emite revokeToken) ID: {self.service_id}, Token: {userToken}.")
        self.publisher.revokeToken(userToken, self.service_id)
