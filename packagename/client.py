import IceFlix
import Ice
import sys
from time import sleep
import hashlib

Ice.loadslice('iceflix.ice')


class Client(Ice.Application):
    def calculate_hash(password):
        sha = hashlib.sha256()
        sha.update(password.encode())
        return sha.hexdigest()

    def run(self, argv):
        broker = self.communicator()
        main_service_proxy = broker.stringToProxy(argv[1])
        connection_tries = 3

        while(connection_tries > 0):
            try:
                check = main_service_proxy.ice_ping()
                if not check:
                    break
            except Exception as ex:
                raise IceFlix.TemporaryUnavailable()
            else:
                connection_tries -= 1
                sleep(10)

        user = input("Introduce el nombre de usuario: ")
        password = input("Password: ")
        hash_password = calculate_hash(password)

        main_connection = IceFlix.MainPrx.checkedCast(main_service_proxy)
        if not main_connection:
            raise RuntimeError("Invalid proxy")

        try:
            authenticator_proxy = main_connection.getAuthenticator()
        except Exception as ex:
            raise IceFlix.TemporaryUnavailable()

        auth_connection = IceFlix.MainPrx.checkedCast(authenticator_proxy)
        if not auth_connection:
            raise RuntimeError("Invalid proxy")

        try:
            auth_token = auth_connection.refreshAuthorization(
                user, hash_password)
        except Exception as ex:
            raise IceFlix.Unauthorized()

        try:
            catalog_proxy = main_connection.getCatalog()
        except Exception as ex:
            raise IceFlix.TemporaryUnavailable()


if __name__ == '__main__':
    sys.exit(Client().main(sys.argv))
