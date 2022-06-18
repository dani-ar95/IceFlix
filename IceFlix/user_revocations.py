""" Modulo para manejar la comunicación al eliminar usuarios o tokens """

import os
import threading
import Ice

try:
    import IceFlix
except ImportError:
    Ice.loadSlice(os.path.join(os.path.dirname(__file__), "iceflix.ice"))
    import IceFlix

class RevocationsListener(IceFlix.Revocations):
    """ Listener del topic Revocations"""

    def __init__(self, own_servant, own_proxy=None, own_service_id=None, own_type=None):
        """ Inicialización del listener """

        self.servant = own_servant
        self.service_id = own_service_id
        self.own_type = own_type
        self.service = own_proxy

    def revokeToken(self, userToken, srvId, current=None):
        """ Comportamiento al recibir un mensaje revokeToken """
        if self.service is not None:
            
            if self.service.ice_isA("::IceFlix::Authenticator"):
                self.servant.remove_token(userToken)
                print("[REVOCATIONS] Token revoked: ", userToken)
                
            if self.service.ice_isA("::IceFlix::StreamController"):
                self.servant.authentication_timer = threading.Timer(5.0, self.servant.stop)
                self.servant.authentication_timer.start()
                
        else:
            if self.servant.logged:
                print("cliente logeado sin token activo")
                self.servant.refreshed_token = False
                try:
                    auth = self.servant._main_prx_.getAuthenticator()
                    new_token = auth.refreshAuthorization(self.servant._username_, self.servant._password_hash_)
                    self.servant._user_token_ = new_token
                    self.servant.refreshed_token = True
                    print("[REVOCATIONS] Token actualizao: ", new_token)
                except IceFlix.TemporaryUnavailable:
                    print("No se ha encontrado ningún servicio de Autenticación")
                    self.servant.logout()
                except IceFlix.Unauthorized:
                    print("Crendeciales no válidas")
                    self.servant.logout()
                
    def revokeUser(self, user, srvId, current=None):
        """ Comportamiento al recibir un mensaje revokeUser """

        if srvId is not self.service_id:
            self.servant.remove_local_user(user)


class RevocationsSender:
    """ Sender del topic Revocations """

    def __init__(self, topic, service_id=None, servant_proxy=None, current=None):
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
        self.publisher.revokeToken(userToken, self.service_id)
