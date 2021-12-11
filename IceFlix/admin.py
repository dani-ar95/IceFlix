#!/usr/bin/python3

from MediaUploader import MediaUploaderI
from os import system, terminal_size, path
import Ice
import sys
from time import sleep
import hashlib
import getpass
import socket
import iceflixrtsp

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")
Ice.loadSlice(SLICE_PATH)
import IceFlix


class Admin(Ice.Application):

    def calculate_hash(self, password):
        sha = hashlib.sha256()
        sha.update(password.encode())
        return sha.hexdigest()

    def format_prompt(self):
        ''' Formatea la consola '''
        system("clear")
        print("         #--------------#")
        print("         | Admin Client |")
        print("         #--------------#\n\n")

    def logged_prompt(self, main_connection, admin_token):
        self.format_prompt()
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
        try:
            catalog_proxy = main_connection.getCatalog()
        except IceFlix.TemporaryUnavailable:
            print("Servicio de catálogo no disponible")
            sys.exit(1)

        while 1:
            system("clear")
            print("Opciones disponibles")
            print("1. Servicio de catálogo")
            print("2. Servicio de autenticación")
            print("3. Servicio de Streaming")
            print("4. Cerrar sesión")
            print("5. Salir del cliente\n")

            option = input("Admin_MainService@" + user + "> ")

            while option.isdigit() == False or int(option) < 1 or int(option) > 5:
                option = input("Inserta una opción válida: ")

            if option == "1":
                self.catalog_service(user, auth_token, catalog_proxy, admin_token)

            elif option == "2":
                self.authenticator_service(user, auth_token, authenticator_proxy, admin_token)

            elif option == "3":
                self.stream_provider_service(admin_token, user)

            elif option == "4":
                print("Cerrando sesión...")
                sleep(2)
                self.not_logged_prompt(main_connection)

            elif option == "5":
                self.communicator.destroy()

    def not_logged_prompt(self, main_connection):
        try:
            catalog_proxy = main_connection.getCatalog()
        except IceFlix.TemporaryUnavailable:
            print("Servicio de catálogo no disponible")
            sys.exit(1)

        while 1:
            system("clear")

            print("1. Servicio de catalogo")
            print("2. Iniciar sesión")
            print("3. Salir del cliente\n")

            option = input("Admin_MainService@Usuario_anonimo> ")
            while option.isdigit() == False or int(option) < 1 or int(option) > 3:
                option = input("Inserta una opción válida: ")

            if option == "1":
                self.not_logged_catalog_service(catalog_proxy)

            elif option == "2":
                self.logged_prompt(main_connection)

            elif option == "3":
                Ice.exit(0)

    def not_logged_catalog_service(self, catalog_connection):
        while 1:
            system("clear")
            print("Opciones disponibles:")
            print("1. Búsqueda por nombre")
            print("2. Volver\n")
            
            option = input("CatalogService@Usuario_anonimo> ")
            while option.isdigit() == False or int(option) < 1 or int(option) > 3:
                option = input("Inserta una opción válida: ")
            
            if option == "1":
                media_list = self.name_searching(catalog_connection)
                if len(media_list) == 0:
                    print("No se han encontrado resultados")
                else:
                    for media in media_list:
                        print(path.split(media.info.name)[1])
                input("Pulsa enter para continuar...")

    def authenticator_service(self, user, auth_token, auth_connection, admin_token):
        ''' Gestiona el comando "authenticator" '''
        # MENU PARA ELEGIR LAS DISTINTAS BUSQUEDAS
        # try:
        while 1:
            system("clear")

            print("1. Añadir usuario")
            print("2. Eliminar usuario")
            print("3. Salir")

            option = input("Admin_AuthenticatorService@" + user + "> ")
            while option.isdigit() == False or int(option) < 1 or int(option) > 3:
                option = input("Inserta una opción válida: ")

            if option == "1":
                new_user = input("Introduce el nuevo nombre de usuario: ")
                new_password = getpass.getpass("Nueva Password: ")
                new_hash_password = self.calculate_hash(new_password)
                auth_connection.addUser(new_user, new_hash_password, admin_token)
                continue
            
            elif option == "2":
                delete_user = input("Introduce un usuario válido para eliminarlo: ")
                auth_connection.removeUser(delete_user, admin_token)
                continue
            
            elif option == "3":
                return 0

    def catalog_service(self, user, auth_token, catalog_connection, admin_token):
        ''' Gestiona el comando "catalog_service" '''
        # MENU PARA ELEGIR LAS DISTINTAS BUSQUEDAS
        # try:
        while 1:
            system("clear")

            print("1. Búsqueda por nombre")
            print("2. Búsqueda por etiquetas")
            print("3. Volver\n")

            option = input("Admin_CatalogService@" + user + "> ")
            while option.isdigit() == False or int(option) < 1 or int(option) > 3:
                option = input("Inserta una opción válida: ")

            if option == "1":
                media_list = self.name_searching(catalog_connection)
                if len(media_list) == 0:
                    print("No se han encontrado resultados")
                    continue
                
                selected_media = self.select_media(media_list)
                if selected_media == -1:
                    continue

                try:
                    self.ask_function(user ,selected_media, auth_token, catalog_connection, admin_token)
                except (IceFlix.Unauthorized, IceFlix.WrongMediaId) as e:
                    print(e)
                else:
                    continue
                
            elif option == "2":
                media_list = self.tag_searching(auth_token, catalog_connection)
                if media_list == None:
                    print("No se han encontrado resultados")
                    continue
                
                selected_media = self.select_media(media_list)
                if selected_media == -1:
                    continue
                
                try:
                    self.ask_function(user ,selected_media, auth_token, catalog_connection)
                except (IceFlix.Unauthorized, IceFlix.WrongMediaId) as e:
                    print(e)
                else:
                    continue

            elif option == "3":
                return 0

    def connect_stream_provider(self):
        stream_provider_proxy = input("Introduce el proxy del stream provider: ")
        proxy = self.communicator().stringToProxy(stream_provider_proxy)
        stream_provider_connection = IceFlix.StreamProviderPrx.checkedCast(proxy)
        try:
            check = stream_provider_connection.ice_ping()
        except Ice.ConnectionRefusedException:
            print("No ha sido posible conectar con Stream Provider")
            return 0
        return stream_provider_connection

    def stream_provider_service(self, admin_token, user):
         while 1:
            system("clear")
            print("Opciones disponibles:")
            print("1. Subir un video")
            print("2. Volver\n")
            
            option = input("Admin_StreamProviderService@" + user + "> ")
            while option.isdigit() == False or int(option) < 1 or int(option) > 3:
                option = input("Inserta una opción válida: ")

            if option == "1":
                stream_provider_connection = self.connect_stream_provider()
                filename = input("Escribe el nombre del video que quieres subir: ")
                file = path.join(path.dirname(__file__), "local/" + filename)
                uploader = MediaUploaderI(file)
                adapter = self.communicator().createObjectAdapterWithEndpoints('MediaUploaderAdapter', 'tcp -p 9100')
                uploader_proxy = adapter.add(uploader, self.communicator().stringToIdentity('MediaUploader'))
                uploader_connection = IceFlix.MediaUploaderPrx.checkedCast(uploader_proxy)
                adapter.activate()
                uploader_connection.ice_ping()
                try:
                    file_id = stream_provider_connection.uploadMedia(file, uploader_connection, admin_token)
                    uploader_connection.close()
                    adapter.destroy()
                except (IceFlix.Unauthorized, IceFlix.UploadError) as e:
                    raise e
            
            elif option == "2":
                return 0

    def stream_provider(self, media, auth_token):
        try:
            stream_controller_proxy = media.provider.getStream(media.mediaId, auth_token)
        except (IceFlix.Unauthorized, IceFlix.WrongMediaId) as e:
            raise e
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("", 10000))
            try:
                config = stream_controller_proxy.getSDP(auth_token, 10000)
                print("Exito en el controller")
            except IceFlix.Unauthorized:
                print("Usuario no autorizado")
                return
            print("config")
            lista = config.split("::")
            emitter = iceflixrtsp.RTSPEmitter(lista[0], lista[1], lista[2])
            emitter.start()
            player = iceflixrtsp.RTSPPlayer()
            player.play(emitter.playback_uri)

            emitter.wait()
            player.stop()
            sock.close()

    def manage_tags(self, media_object, auth_token, catalog_connection, is_add):
        tags_list = self.ask_for_tags()

        if is_add:  # Añadir etiquetas
            try:
                catalog_connection.addTags(media_object.mediaId, tags_list, auth_token)
            except (IceFlix.Unauthorized, IceFlix.WrongMediaId) as e:
                print(e)
                raise e
            else:
                print("Etiquetas añadidas correctamente")

        else:   # Eliminar etiquetas
            try:
                catalog_connection.removeTags(media_object.mediaId, tags_list, auth_token)
            except (IceFlix.Unauthorized, IceFlix.WrongMediaId) as e:
                print(e)
                raise e
            else:
                print("Etiquetas eliminadas correctamente")

        return 0

    def tag_searching(self, auth_token, catalog_connection):
        media_list = []
        tag_list = self.ask_for_tags()

        if not tag_list:
            return 0

        option = input(
            "¿Quieres que tu búsqueda coincida con todas tus etiquetas? (s/n): ")
        while option != "s" and option != "n":
            option = input("Inserta una opción válida: ")

        all_tags = None
        if option == "s":
            all_tags = True
        elif option == "n":
            all_tags = False

        try:
            id_list = catalog_connection.getTilesByTags(
                tag_list, all_tags, auth_token)
        except IceFlix.Unauthorized:
            print("Usuario no autorizado.")
            return

        for id in id_list:
            try:
                media_list.append(catalog_connection.getTile(id))
            except(IceFlix.WrongMediaId, IceFlix.TemporaryUnavailable) as e:
                print(e)

        return media_list

    def name_searching(self, catalog_connection):
        media_list = []
        full_title = False
        print("\nOpciones disponibles:")
        print("1. Buscar medio por nombre completo")
        print("2. Buscar medio por parte del nombre\n")
        option = input("Opción (1/2): ")
        while option.isdigit() == False or int(option) < 1 or int(option) > 2:
            option = input("Inserta una opción válida: ")

        if option == "1":
            full_title = True
        elif option == "2":
            full_title = False

        title = input("\nInsertar titulo: ")

        id_list = catalog_connection.getTilesByName(title, full_title)

        for id in id_list:
            try:
                media_list.append(catalog_connection.getTile(id))
            except (IceFlix.WrongMediaId, IceFlix.TemporaryUnavailable) as e:
                print(e)

        return media_list

    def select_media(self, media_list):
        counter = 0
        print("Media encontrado:\n")
        for media in media_list:
            counter += 1
            print(str(counter) + ". " + path.split(media.info.name)[1])

        option = input(
            "Selecciona un media o deja en blanco para salir: ")
        while option.isdigit() == False or int(option) < 1 or int(option) > counter:
            if option == "":
                return -1
            option = input("Inserta una opción válida: ")        

        selected_media = media_list[int(option)-1]
        return selected_media

    def ask_function(self, user, media_object, auth_token, catalog_connection, admin_token):
        print("1. Reproducir")
        print("2. Añadir etiquetas")
        print("3. Eliminar etiquetas")
        print("4. Renombra título")
        print("5. Eliminar video")
        
        option = input("Admin_CatalogService@" + user + "> ")
        while option.isdigit() == False or int(option) < 1 or int(option) > 5:
            option = input("Inserta una opción válida: ")
            
        if option == "1":
            try:
                self.stream_provider(media_object, auth_token)
            except (IceFlix.Unauthorized, IceFlix.WrongMediaId) as e:
                print(e)
                input("Presiona Enter para continuar...")
            
        elif option == "2":
            try:
                self.manage_tags(media_object, auth_token, catalog_connection, True)
            except (IceFlix.Unauthorized, IceFlix.WrongMediaId) as e:
                print(e)
                input("Presiona Enter para continuar...")
            
        elif option == "3":
            try:
                self.manage_tags(media_object, auth_token, catalog_connection, False)
            except (IceFlix.Unauthorized, IceFlix.WrongMediaId) as e:
                print(e)
                input("Presiona Enter para continuar...")

        elif option == "4":
            try:
                self.renameTile(media_object, catalog_connection, admin_token)
            except (IceFlix.Unathorized, IceFlix.WrongMediaId) as e:
                print(e)
                input("Presiona Enter para continuar...")
            print("Título renombrado correctamente")
            input("Presiona Enter para continuar...")

        elif option == "5":
            stream_provider_connection = self.connect_stream_provider()
            try:
                stream_provider_connection.deleteMedia(media_object.mediaId, admin_token)
            except (IceFlix.Unauthorized, IceFlix.WrongMediaId) as e:
                print(e)
                input("Presiona Enter para continuar...")
            print("Video borrado correctamente")
            input("Presiona Enter para continuar...")


    def renameTile(media_object,catalog_connection,admin_token):
        new_name = input("Nuevo nombre: ")
        catalog_connection.renameTile(media_object.mediaId,new_name,admin_token)

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
        
        if len(argv) > 2:
            is_admin = main_connection.isAdmin(argv[2])
            if is_admin:
                login = input("Quieres logearte? (s/n): ")
                if login == "s":
                    self.logged_prompt(main_connection, argv[2])

                elif login == "n":
                    self.not_logged_prompt(main_connection)
            else:
                print("The admin token is not valid. Please retry again")
        else:
            print("Please retry introducing an admin token")

        print("Press Ctrl+C to exit")
        self.shutdownOnInterrupt()
        broker.waitForShutdown()


if __name__ == '__main__':
    sys.exit(Admin().main(sys.argv))
