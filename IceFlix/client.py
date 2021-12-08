#!/usr/bin/python3

<<<<<<< HEAD
=======
import IceFlix
>>>>>>> d47aef0dfda55e460d01e45a9cac2be7d1ee9b0f
from os import system, terminal_size
import Ice
import sys
from time import sleep
import hashlib
import getpass
import socket
import iceflixrtsp

Ice.loadSlice("./iceflix.ice")

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
            sys.exit(1)

        try:
            auth_token = authenticator_proxy.refreshAuthorization(
                user, hash_password)
        except IceFlix.Unauthorized:
            print("Credenciales invalidas. Ejecutando modo usuario anónimo...")
            sleep(2)  # Simula complejidad
            system("clear")
            self.not_logged_prompt(main_connection)
<<<<<<< HEAD
            
=======

>>>>>>> d47aef0dfda55e460d01e45a9cac2be7d1ee9b0f
        try:
            catalog_proxy = main_connection.getCatalog()
        except IceFlix.TemporaryUnavailable:
            print("Servicio de catálogo no disponible")
            sys.exit(1)
<<<<<<< HEAD
            
        while 1:
            keyboard = input("MainService@" + user + "> ")
            if keyboard == "catalog_service":
                self.catalog_service(user, auth_token, catalog_proxy)
                
=======

        while 1:
            keyboard = input("MainService@" + user + "> ")
            if keyboard == "catalog_service":
                self.catalog_service(user, auth_token, main_connection)

>>>>>>> d47aef0dfda55e460d01e45a9cac2be7d1ee9b0f
            elif keyboard == "logout":
                print("Cerrando sesión...")
                system("clear")
                self.not_logged_prompt(main_connection)
<<<<<<< HEAD
            
            
    def not_logged_prompt(self, main_connection):
        while 1:
                keyboard = input("MainService@Usuario_anonimo> ")
                if keyboard == "catalog_service":
                    self.catalog_service()
                elif keyboard == "exit":
                    sys.exit(0)
                elif keyboard == "login":
                    self.logged_prompt(main_connection)
        
        
    def catalog_service(self, user, auth_token, catalog_connection):
        ''' Gestiona el comando "catalog_service" '''
        #MENU PARA ELEGIR LAS DISTINTAS BUSQUEDAS
        #try:
        while 1:
            system("clear")
            
=======

    def not_logged_prompt(self, main_connection):
        while 1:
            keyboard = input("MainService@Usuario_anonimo> ")
            if keyboard == "catalog_service":
                self.catalog_service()
            elif keyboard == "exit":
                sys.exit(0)
            elif keyboard == "login":
                self.logged_prompt(main_connection)

    def catalog_service(self, user, auth_token, main_connection):
        ''' Gestiona el comando "catalog_service" '''
        # MENU PARA ELEGIR LAS DISTINTAS BUSQUEDAS
        # try:
        while 1:
            system("clear")

>>>>>>> d47aef0dfda55e460d01e45a9cac2be7d1ee9b0f
            print("1. Búsqueda por nombre")
            print("2. Búsqueda por etiquetas")
            print("3. Añadir etiquetas")
            print("4. Eliminar etiqutetas")
            print("5. Salir")
<<<<<<< HEAD
            
            option = input(user + "> ")
            while option.isdigit() == False or int(option) < 1 or int(option) > 4:
                    option = input("Inserta una opción válida: ")
            
            if option == "1":
                media_list = self.name_searching(catalog_connection)
                if media_list == None:
                    return 
                
            elif option == "2":
                media_list = self.tag_searching(auth_token, catalog_connection)
                if media_list == None:
                    return
                
=======

            option = input(user + "> ")
            while option.isdigit() == False or int(option) < 1 or int(option) > 4:
                option = input("Inserta una opción válida: ")

            if option == "1":
                media_list = self.name_searching(main_connection)
                if media_list == None:
                    return

            elif option == "2":
                media_list = self.tag_searching(auth_token, main_connection)
                if media_list == None:
                    return

>>>>>>> d47aef0dfda55e460d01e45a9cac2be7d1ee9b0f
            elif option == "3":
                pass
            elif option == "5":
                return
<<<<<<< HEAD
            
=======

>>>>>>> d47aef0dfda55e460d01e45a9cac2be7d1ee9b0f
            counter = 0
            print("Media encontrado:\n")
            for media in media_list:
                counter += 1
                print(str(counter) + media.info.name)
<<<<<<< HEAD
            
            selecting_media = input("Selecciona un media (1-" + str(counter) + "), o deja en blanco para realizar otra búsqueda: ")
            while selecting_media.isdigit() == False or int(selecting_media) < 1 or int(selecting_media) > counter or selecting_media != "":
                selecting_media = input("Inserta una opción válida: ")
        
            if not selecting_media:
                return
            else: 
                self.stream_provider(media_list[int(selecting_media) - 1])
            
            
=======

            selecting_media = input(
                "Selecciona un media (1-" + str(counter) + "), o deja en blanco para realizar otra búsqueda: ")
            while selecting_media.isdigit() == False or int(selecting_media) < 1 or int(selecting_media) > counter or selecting_media != "":
                selecting_media = input("Inserta una opción válida: ")

            if not selecting_media:
                return
            else:
                self.stream_provider(media_list[int(selecting_media) - 1])

>>>>>>> d47aef0dfda55e460d01e45a9cac2be7d1ee9b0f
    def stream_provider(self, media, auth_token):
        #media.provider = IceFlix.StreamProviderPrx.checkedCast(media.provider)

        try:
<<<<<<< HEAD
            stream_controller_proxy = media.provider.getStream(media.id, auth_token)
        except (IceFlix.Unauthorized, IceFlix.WrongMediaId) as e:  
            print(e)
            return
        
=======
            stream_controller_proxy = media.provider.getStream(
                media.id, auth_token)
        except (IceFlix.Unauthorized, IceFlix.WrongMediaId) as e:
            print(e)
            return

>>>>>>> d47aef0dfda55e460d01e45a9cac2be7d1ee9b0f
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("", 10000))
        try:
            config = stream_controller_proxy.getSDP(auth_token, 10000)
        except IceFlix.Unauthorized:
            print("Usuario no autorizado")
            return
        lista = config.split("::")
        emitter = iceflixrtsp.RTSPEmitter(lista[0], lista[1], lista[2])
        emitter.start()
        player = iceflixrtsp.RTSPPlayer()
        player.play(emitter.playback_uri)

        # Stream for 10 seconds
        sleep(10.0)

        # Stop player and streamer
        player.stop()
        emitter.stop()

<<<<<<< HEAD
        
    def tag_searching(self, auth_token, catalog_connection):
        media_list = []
        tag_list = []
        
=======
    def tag_searching(self, auth_token, catalog_connection):
        media_list = []
        tag_list = []

>>>>>>> d47aef0dfda55e460d01e45a9cac2be7d1ee9b0f
        print("Inserta sus etiquetas. Para salir, dejar en blanco:")
        while 1:
            tag = input("Etiqueta: ")
            if tag == "":
                break
<<<<<<< HEAD
            tag_list.append(tag)    
        
        if not tag_list:
            return
        
        option = input("¿Quieres que tu búsqueda coincida con todas tus etiquetas? (s/n): ")
=======
            tag_list.append(tag)

        if not tag_list:
            return

        option = input(
            "¿Quieres que tu búsqueda coincida con todas tus etiquetas? (s/n): ")
>>>>>>> d47aef0dfda55e460d01e45a9cac2be7d1ee9b0f
        while option != "s" and option != "n":
            option = input("Inserta una opción válida: ")

        all_tags = None
        if option == "s":
            all_tags = True
        elif option == "n":
            all_tags = False
<<<<<<< HEAD
            
        try:
            id_list = catalog_connection.searchByTags(tag_list, all_tags, auth_token)
        except IceFlix.Unauthorized:
            print("Usuario no autorizado.")
            return
        
=======

        try:
            id_list = catalog_connection.searchByTags(
                tag_list, all_tags, auth_token)
        except IceFlix.Unauthorized:
            print("Usuario no autorizado.")
            return

>>>>>>> d47aef0dfda55e460d01e45a9cac2be7d1ee9b0f
        for id in id_list:
            try:
                media_list.append(catalog_connection.getTile(id))
            except(IceFlix.WrongMediaId, IceFlix.TemporaryUnavailable) as e:
                print(e)
<<<<<<< HEAD
                
        return media_list
    
    def name_searching(self, catalog_connection):
        media_list = []
        full_title = False
        
=======

        return media_list

    def name_searching(self, catalog_connection):
        media_list = []
        full_title = False

>>>>>>> d47aef0dfda55e460d01e45a9cac2be7d1ee9b0f
        print("1. Buscar por nombre completo")
        print("2. Buscar por parte del nombre")
        option = input("Opción (1/2): ")
        while option.isdigit() == False or int(option) < 1 or int(option) > 2:
            option = input("Inserta una opción válida: ")
<<<<<<< HEAD
            
=======

>>>>>>> d47aef0dfda55e460d01e45a9cac2be7d1ee9b0f
        if option == "1":
            full_title = True
        elif option == "2":
            full_title = False
<<<<<<< HEAD
        
        title = input("\nInsertar titulo: ")
        
=======

        title = input("\nInsertar titulo: ")

>>>>>>> d47aef0dfda55e460d01e45a9cac2be7d1ee9b0f
        id_list = catalog_connection.getTilesByName(title, full_title)

        for id in id_list:
            try:
                media_list.append(catalog_connection.getTile(id))
            except (IceFlix.WrongMediaId, IceFlix.TemporaryUnavailable) as e:
                print(e)
<<<<<<< HEAD
                        
=======

>>>>>>> d47aef0dfda55e460d01e45a9cac2be7d1ee9b0f
        return media_list

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
                print(
                    "No ha sido posible conectar con Main Service. Intentando de nuevo en 10s...")
                connection_tries -= 1
                if connection_tries == 0:
                    print("Número máximo de intentos alcanzados. Saliendo...")
                    sleep(2)
                    return 0
                sleep(1)  # cambiar a 10 segundoss

        main_connection = IceFlix.MainPrx.checkedCast(main_service_proxy)
<<<<<<< HEAD
            
=======

>>>>>>> d47aef0dfda55e460d01e45a9cac2be7d1ee9b0f
        login = input("Quieres logearte? (s/n): ")
        if login == "s":
            self.logged_prompt(main_connection)

        elif login == "n":
            self.not_logged_prompt(main_connection)

        self.shutdownOnInterrupt()
        broker.waitForShutdown()


if __name__ == '__main__':
    sys.exit(Client().main(sys.argv))
