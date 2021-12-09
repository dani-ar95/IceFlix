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

EXIT_OK = 0
EXIT_ERROR = 1


class Admin(Ice.Application):

    def calculate_hash(self, password):
        sha = hashlib.sha256()
        sha.update(password.encode())
        return sha.hexdigest()

    def logged_prompt(self, main_connection, admin_token):
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
            keyboard = input("MainService@" + user + "> ")
            if keyboard == "catalog_service":
                self.catalog_service(user, auth_token, catalog_proxy, admin_token)
            elif keyboard == "authenticator":
                self.authenticator_service(user, auth_token, authenticator_proxy, admin_token)
            elif keyboard == "streamprovider":
                self.stream_provider_service(admin_token)
            elif keyboard == "logout":
                print("Cerrando sesión...")
                system("clear")
                self.not_logged_prompt(main_connection)

    def not_logged_prompt(self, main_connection):
        while 1:
            keyboard = input("MainService@Usuario_anonimo> ")
            if keyboard == "catalog_service":
                self.catalog_service()
            elif keyboard == "exit":
                sys.exit(0)
            elif keyboard == "login":
                self.logged_prompt(main_connection)

    def authenticator_service(self, user, auth_token, auth_connection, admin_token):
        ''' Gestiona el comando "authenticator" '''
        # MENU PARA ELEGIR LAS DISTINTAS BUSQUEDAS
        # try:
        while 1:
            system("clear")
            print("1. whois")
            print("2. Añadir usuario")
            print("3. Eliminar usuario")
            print("4. Salir")

            option = input(user + "> ")
            while option.isdigit() == False or int(option) < 1 or int(option) > 4:
                option = input("Inserta una opción válida: ")

            if option == "1":
                user = auth_connection.whois(auth_token)
                print(user)
                sleep(2)
            elif option == "2":
                new_user = input("Introduce el nuevo nombre de usuario: ")
                new_password = getpass.getpass("Nueva Password: ")
                new_hash_password = self.calculate_hash(new_password)
                auth_connection.addUser(new_user, new_hash_password, admin_token)
            elif option == "3":
                delete_user = input("Introduce un usuario válido para eliminarlo: ")
                auth_connection.removeUser(delete_user, admin_token)
            elif option == "4":
                return

    def catalog_service(self, user, auth_token, catalog_connection, admin_token):
        ''' Gestiona el comando "catalog_service" '''
        # MENU PARA ELEGIR LAS DISTINTAS BUSQUEDAS
        # try:
        while 1:
            system("clear")

            print("1. Búsqueda por nombre")
            print("2. Búsqueda por etiquetas")
            print("5. Salir")

            option = input(user + "> ")
            while option.isdigit() == False or int(option) < 1 or int(option) > 5:
                option = input("Inserta una opción válida: ")

            if option == "1":
                media_list = self.name_searching(catalog_connection)
                if media_list == None:
                    return
                print("Estas son las medias disponibles: ")
                for media in media_list:
                    print(media.info.name)
                option = input("Elige una media: ")
                media_elegida = media_list[int(option)]
                print("Opciones: ")
                print("0. Añadir etiquetas")
                print("1. Eliminar etiquetas")
                print("2. Reproducir")
                print("3. Renombra nombra")
                print("4. Eliminar video")
                option = input("Elige una opcion: ")
                if option == "1":
                    print("Introcuce las etiquetas que quieras de una en una")
                    etiqueta = input("Etiqueta:")
                    try:
                        catalog_connection.addTags(media_elegida.mediaId, [etiqueta], auth_token)
                    except (IceFlix.Unauthorized, IceFlix.WrongMediaId) as e:
                        raise e
                return
                
            elif option == "2":
                media_list = self.tag_searching(auth_token, catalog_connection)
                if media_list == None:
                    return

            elif option == "3":
                
                pass
            elif option == "5":
                return
            
            '''counter = 0
            print("Media encontrado:\n")
            for media in media_list:
                counter += 1
                print(str(counter) + media.info.name)

            selecting_media = input(
                "Selecciona un media (1-" + str(counter) + "), o deja en blanco para realizar otra búsqueda: ")
            while selecting_media.isdigit() == False or int(selecting_media) < 1 or int(selecting_media) > counter or selecting_media != "":
                selecting_media = input("Inserta una opción válida: ")

            if not selecting_media:
                return
            else:
                self.stream_provider(media_list[int(selecting_media) - 1])'''

    def stream_provider_service(self, admin_token):
        stream_provider_proxy = input("Introduce el proxy del stream provider: ")
        proxy = self.communicator().stringToProxy(stream_provider_proxy)
        stream_provider_connection = IceFlix.StreamProviderPrx.checkedCast(proxy)
        try:
            check = stream_provider_connection.ice_ping()
        except Ice.ConnectionRefusedException:
            print("No ha sido posible conectar con Stream Provider")
            return
        filename = input("Escribe el nombre del video que quieres subir: ")
        file = path.join(path.dirname(__file__), filename)
        uploader = MediaUploaderI(file)
        adapter = self.communicator().createObjectAdapterWithEndpoints('MediaUploaderAdapter', 'tcp -p 9080')
        uploader_proxy = adapter.add(uploader, self.communicator().stringToIdentity('MediaUploader'))
        uploader_connection = IceFlix.MediaUploaderPrx.checkedCast(uploader_proxy)
        try:
            file_id = stream_provider_connection.uploadMedia(file, uploader_connection, admin_token)
        except (IceFlix.Unauthorized, IceFlix.UploadError) as e:
            raise e

    def renameTile(media_list,catalog_connection,admin_token):
        option = input("Elige una para renombrarla:")
        new_name = input("Nuevo nombre: ")
        #Controlar que el admin no meta valores ilegales
        catalog_connection.renameTile(media_list[int(option)].mediaId,new_name,admin_token)

    def stream_provider(self, media, auth_token):
        #media.provider = IceFlix.StreamProviderPrx.checkedCast(media.provider)

        try:
            stream_controller_proxy = media.provider.getStream(
                media.id, auth_token)
        except (IceFlix.Unauthorized, IceFlix.WrongMediaId) as e:
            print(e)
            return

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

    def tag_searching(self, auth_token, catalog_connection):
        media_list = []
        tag_list = []

        print("Inserta sus etiquetas. Para salir, dejar en blanco:")
        while 1:
            tag = input("Etiqueta: ")
            if tag == "":
                break
            tag_list.append(tag)

        if not tag_list:
            return

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
            id_list = catalog_connection.searchByTags(
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

        print("1. Buscar por nombre completo")
        print("2. Buscar por parte del nombre")
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
