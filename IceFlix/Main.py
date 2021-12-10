#!/usr/bin/python3
# pylint: disable=invalid-name
"""Modulo Servicio Principal"""

from os import path
import sys
import Ice

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")

try:
    import IceFlix
except ImportError:
    Ice.loadSlice(SLICE_PATH)
    import IceFlix

class MainI(IceFlix.Main): # pylint: disable=inherit-non-class
    """Sirviente del servicio principal"""

    def __init__(self):
        self._servants_ = set()

    def getAuthenticator(self, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Devuelve el proxy a un Servicio de Autenticación válido registrado '''

        for servant in self._servants_:
            try:
                is_auth = servant.ice_isA("::IceFlix::Authenticator")
            except Ice.ConnectionRefusedException:
                break
            else:
                if is_auth:
                    if servant.ice_isA("::IceFlix::Authenticator"):
                        try:
                            response = servant.ice_ping()
                        except Ice.ConnectionRefusedException:
                            self._servants_.remove(servant)
                        if not response:
                            return IceFlix.AuthenticatorPrx.checkedCast(servant)

        raise IceFlix.TemporaryUnavailable

    def getCatalog(self, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Devuelve el proxy a un Servicio de Catálogo válido registrado '''

        for servant in self._servants_:
            try:
                is_catalog = servant.ice_isA("::IceFlix::MediaCatalog")
            except Ice.ConnectionRefusedException:
                break
            else:
                if is_catalog:
                    try:
                        response = servant.ice_ping()
                    except Ice.ConnectionRefusedException:
                        self._servants_.remove(servant)
                    if not response:
                        return IceFlix.MediaCatalogPrx.checkedCast(servant)

        raise IceFlix.TemporaryUnavailable

    def register(self, service, current=None): # pylint: disable=unused-argument
        ''' Permite registrarse a determinados servicios '''

        self._servants_.add(service)
        # Throws UnkownService

    def isAdmin(self, adminToken, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Verifica que un token es de administración '''
        return adminToken == self._token_ # pylint: disable=invalid-name

class MainServer(Ice.Application):
    """Servidor del servicio principal"""
    def run(self):
        ''' Implementación del servidor principal '''
        broker = self.communicator()
        servant = MainI()
        properties = broker.getProperties()
        servant._token_ = properties.getProperty("AdminToken")

        adapter = broker.createObjectAdapter("MainAdapter")
        adapter.add(servant, broker.stringToIdentity("Main"))

        adapter.activate()

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0

if __name__ == "__main__":
    sys.exit(MainServer().main(sys.argv))
