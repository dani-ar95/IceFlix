import Ice
import sys
from time import sleep

Ice.loadslice('iceflix.ice')
import IceFlix

class Client(Ice.Application):
    def run(self, argv):
        broker = self.communicator()
        main_service_proxy = broker.stringToProxy(argv[1])
        connection_tries = 3
        
        while(connection_tries>0):
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
        
        
        
if __name__ == '__main__':
    sys.exit(Client().main(sys.argv))