#!/usr/bin/python3

from os import system
import Ice
import sys
from time import sleep
import hashlib
import getpass
import signal

Ice.loadSlice("./iceflix.ice")
import IceFlix

EXIT_OK = 0
EXIT_ERROR = 1

class Client(Ice.Application):
   
    def calculate_hash(self, password):
        sha = hashlib.sha256()
        sha.update(password.encode())
        return sha.hexdigest()
    
    def logged_prompt(self, main_connection):
        user = input("Introduce el nombre de usuario: ")
        password = getpass.getpass("Password: ")
        hash_password = self.calculate_hash(password)

        
        try:
            print("Conectando con el servicio de autenticación...")
            authenticator_proxy = main_connection.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            print("Servicio de autenticación no disponible.")
            sys.exit(0)


        #auth_connection = IceFlix.MainPrx.checkedCast(authenticator_proxy)
        auth_connection = authenticator_proxy
        try:    
            auth_token = auth_connection.refreshAuthorization(user, hash_password)
        except IceFlix.Unauthorized:
            print("Credenciales invalidas. Ejecutando modo usuario anónimo...")
            sleep(2)
            self.not_logged_prompt(main_connection)
            
        while 1:
            keyboard = input(user+" >: ")
            if keyboard == "logout":
                print("Cerrando sesión...")
                system("clear")
                return 0
            pass
            
    def not_logged_prompt(self, main_connection):
        while 1:
                keyboard = input("Usuario anonimo >: ")
                if keyboard == "catalog_service":
                    try:
                        catalog_proxy = main_connection.getCatalog()
                    except IceFlix.TemporaryUnavailable:
                        print("Servicio de catálogo no disponible") 
                    else:
                        catalog_connection = IceFlix.MainPrx.checkedCast(catalog_proxy)
                        print("1. Buscar por nombre competo")
                        print("2. Buscar por parte del nombre")
                        option = input("Opción (1/2): ")
                        while option.isdigit() == False or int(option) < 1 or int(option) > 2:
                            option = input("Inserta una opción válida: ")
                        if option == "1":
                            title = input("\nInsertar titulo: ")
                            media_info = catalog_proxy.getTilesByName(title, True)
                            for id in media_info:
                                try:
                                    media = catalog_proxy.getTile(id)
                                except (IceFlix.WrongMediaId, IceFlix.TemporaryUnavailable) as e:
                                    print("El servicio de Streaming asociado a este medio no esta disponible\n")
                        elif option == "2":
                            title = input("\nInsertar titulo: ")
                            id_list = catalog_proxy.getTilesByName(title, False)
                            for id in id_list:
                                print(id)
                                try:
                                    media = catalog_proxy.getTile(id)
                                    print(media.info)
                                except (IceFlix.WrongMediaId, IceFlix.TemporaryUnavailable) as e:
                                    print("El servicio de Streaming asociado a este medio no esta disponible\n")

                elif keyboard == "exit":
                    sys.exit(0)
                elif keyboard == "login":
                    self.logged_prompt(main_connection)
        

    def run(self, argv):
        broker = self.communicator()
        main_service_proxy = broker.stringToProxy(argv[1])
        connection_tries = 3
        
        while(connection_tries > 0):
            try:
                check = main_service_proxy.ice_ping()
                if not check:
                    break
            except Ice.ConnectionRefusedException:
                print("No ha sido posible conectar con Main Service. Intentando de nuevo en 10s...")
                connection_tries -= 1
                if connection_tries == 0:
                    print("Número máximo de intentos alcanzados. Saliendo...")
                    sleep(2)
                    return 0
                sleep(1) #cambiar a 10 segundoss

        main_connection = IceFlix.MainPrx.checkedCast(main_service_proxy)
            
        login = input("Quieres logearte? (y/n): ")
        if login == "y":
            self.logged_prompt(main_connection)
            
        elif login == "n":
            self.not_logged_prompt(main_connection)
        
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

if __name__ == '__main__':
    sys.exit(Client().main(sys.argv))
