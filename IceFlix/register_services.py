""" Módulo para registrar nuevos servicios anunciados """

import os
import Ice

try:
    import IceFlix
except ImportError:
    Ice.loadSlice(os.path.join(os.path.dirname(__file__), "iceflix.ice"))
    import IceFlix

class RegisterServices(IceFlix.ServiceAnnouncements):
    """Registra los servicios de autenticación y catálogo"""

    def __init__(self, own_servant, own_service_id, own_type):
        self.servant = own_servant
        self.service_id = own_service_id
        self.own_type = own_type

        self.known_ids = set()
        
    def newService(self, service_prx, service_id, current=None):
        if service_id == self.service_id or service_id in self.known_ids:
            return
   
        if service_prx.ice_isA("::IceFlix::Authenticator"):
            self.servant.auth_services.append(service_prx)
            self.known_ids.add(service_id)
            print("[MAIN] Se ha registrado el servicio de autenticación: ", service_id)

        if service_prx.ice_isA("::IceFlix::MediaCatalog"):
            self.servant.catalog_services.append(service_prx)
            self.known_ids.add(service_id)
            print("[MAIN] Se ha registrado el servicio de catálogo: ", service_id)
    
    def announce(self, service_prx, service_id, current = None):
        pass