#!/usr/bin/python3
# pylint: disable=invalid-name
"""Modulo Servicio Principal"""

from os import path
import sys
import Ice

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")

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
                self._servants_.remove(servant)
            else:
                if is_auth:
                    return IceFlix.AuthenticatorPrx.checkedCast(servant)

        raise IceFlix.TemporaryUnavailable

    def getCatalog(self, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Devuelve el proxy a un Servicio de Catálogo válido registrado '''

        for servant in self._servants_:
            try:
                is_catalog = servant.ice_isA("::IceFlix::MediaCatalog")
            except Ice.ConnectionRefusedException:
                self._servants_.remove(servant)
            else:
                if is_catalog:
                    return IceFlix.MediaCatalogPrx.checkedCast(servant)

        raise IceFlix.TemporaryUnavailable


    def register(self, service, current=None): # pylint: disable=unused-argument
        ''' Permite registrarse a determinados servicios '''

        possible_servants = set(["MediaCatalog", "Authenticator", "StreamProvider"])
        print(service.ice_getIdentity())
        if service.ice_getIdentity().name in possible_servants:
            self._servants_.add(service)
        else:
            raise IceFlix.UnknownService

    def isAdmin(self, adminToken, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Verifica que un token es de administración '''
        return adminToken == self._token_ # pylint: disable=invalid-name

class MainServer(Ice.Application):
    """Servidor del servicio principal"""

    def run(self, argv):
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
