#!/usr/bin/python3

import Ice
import sys
from time import sleep
import hashlib
import getpass

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
            pass
            
    def not_logged_prompt(self, main_connection):
        while 1:
                keyboard = input("Usuario anonimo >: ")
                if keyboard == "catalog_service":
                    try:
                        catalog_proxy = main_connection.getCatalog()
                    except IceFlix.TemporaryUnavailable:
<<<<<<< Updated upstream
                        print("Servicio de catálogo no disponible") 
                    else:
                        catalog_connection = IceFlix.MainPrx.checkedCast(catalog_proxy)
                        
=======
                        print("Servicio de catálogo no disponible")
                    else:
                        print("Catálogo conectado")
                        print("SOlicitas info porque si")
                        # Dar opcion de nombre completo o no
                        print(catalog_proxy.getTitlesByName("Up", False))

>>>>>>> Stashed changes
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
                print("No ha sido posible conectar. Intentando de nuevo...")
                connection_tries -= 1
                if connection_tries == 0:
                    print("Número máximo de intentos alcanzados. Saliendo...")
                    sleep(2)

                sleep(10)

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
