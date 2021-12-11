#!/usr/bin/python3

from MediaUploader import MediaUploaderI
from os import system, terminal_size, path
import Ice
import sys
from time import sleep
import hashlib
import getpass
import iceflixrtsp

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")
Ice.loadSlice(SLICE_PATH)
import IceFlix

class Cliente(Ice.Application):

    def __init__(self):
        self._username_ = None
        self._admin_token_ = None
        self._user_token_ = None
        self._main_prx_ = None
        self._auth_prx_ = None
        self._catalog_prx_ = None
        self._stream_provider_prx_ = None
    
    def format_prompt(self):
        ''' Formatea la consola '''
        system("clear")
        print("         #----------------#")
        print("         | Iceflix Client |")
        print("         #----------------#\n\n")
    
    def get_admin_token(self):
        token = input("Introduce el token de administración: ")
        
        is_admin = self._main_prx_.isAdmin(token)
    
        if is_admin:
            self._admin_token_ = token
        else:
            self._admin_token_ = None
            print("Ese token no corresponde al de administración")
            input("Pulsa Enter para continuar...")

    def set_main_proxy(self):
        proxy = input("Introduce el proxy al servicio principal: ")
        connection_tries = 3
        try:
            main_proxy = self.communicator().stringToProxy(proxy)
        except:
            print("La conexión no ha sido posible")
            sys.exit(1)
        else:
            try:
                main_connection = IceFlix.MainPrx.checkedCast(main_proxy)
            except:
                print("La conexión no ha sido posible")
                sys.exit(1)
            print("Conectando con el servicio principal...")
            sleep(1)    #Simula complejidad
            while(connection_tries > 0):
                try:
                    print("antes del isA")
                    check = main_connection.ice_isA("::IceFlix::Main")
                    if check:
                        break
                except Ice.ConnectionRefusedException:
                    print("No ha sido posible contactar con el servicio principal. Intentando de nuevo en 10s...")
                    connection_tries -= 1
                    if connection_tries == 0:
                        print("Número máximo de intentos alcanzados. Saliendo...")
                        sleep(2)    #Simula complejidad
                        sys.exit(1)
                    sleep(10)  # cambiar a 10 segundoss

            self._main_prx_ = main_connection

            try:
                self._auth_prx_ = self._main_prx_.getAuthenticator()
            except IceFlix.TemporaryUnavailable:
                pass
            try:
                self._catalog_prx_ = self._main_prx_.getCatalog()
            except IceFlix.TemporaryUnavailable:
                pass

    def login(self):
        user = input("Nombre de usuario: ")
        password = getpass.getpass("Contraseña: ")
        hash_password = hashlib.sha256(password.encode()).hexdigest()
        if not self._auth_prx_:
            try:
                self._auth_prx_ = self._main_prx_.getAuthenticator()
            except IceFlix.TemporaryUnavailable:
                print(IceFlix.TemporaryUnavailable)
        try:
            self._user_token_ = self._auth_prx_.refreshAuthorization(user, hash_password)
        except IceFlix.Unauthorized:
            print(IceFlix.Unauthorized)
        else:
            self._username_ = user    

    def logout(self):
        self._username_ = None
        self._user_token_ = None

    def create_prompt(self, servicio: str):
        if self._username_ and self._admin_token_:
            return "Admin>>" + servicio + "@" + self._username_ + "> "
        else:
            if self._username_:
                return servicio + "@" + self._username_ + "> "
            elif self._admin_token_:
                return "Admin>>" + servicio + "@Anónimo> "
            else:
                return servicio + "@Anónimo> "

    def catalog_service(self):
        ''' Gestiona el comando "catalog_service" '''
        #MENU PARA ELEGIR LAS DISTINTAS BUSQUEDAS

        if not self._catalog_prx_:
            try:
                self._catalog_prx_ = self._main_prx_.getCatalog()
            except IceFlix.TemporaryUnavailable:
                print(IceFlix.TemporaryUnavailable)

        while 1:
            system("clear")
            self.format_prompt()
            print("Opciones disponibles:")
            print("1. Búsqueda por nombre")
            print("2. Búsqueda por etiquetas")
            print("3. Volver\n")
            
            option = input(self.create_prompt("CatalogService"))
            while option.isdigit() == False or int(option) < 1 or int(option) > 3:
                if option == "":
                    option = input(self.create_prompt("CatalogService"))
                else:
                    option = input("Inserta una opción válida: ")
            
            if option == "1":
                media_list = self.name_searching()
                if len(media_list) == 0:
                    print("\nNo se han encontrado resultados")
                    input("Pulsa enter para continuar...")
                    continue
                
                selected_media = self.select_media(media_list)
                if selected_media == -1:
                    continue
                
                try:
                    self.ask_function(selected_media)
                except (IceFlix.Unauthorized, IceFlix.WrongMediaId) as e:
                    print(e)
                else:
                    continue
                
            elif option == "2":
                media_list = self.tag_searching()
                if media_list == -1:
                    print("\nNo se han encontrado resultados")
                    input("Pulsa enter para continuar...")
                    continue
                elif media_list == 0:
                    print("No autorizado")
                    input("Pulsa enter para continuar...")
                    continue
                
                selected_media = self.select_media(media_list)
                if selected_media == -1:
                    continue
                
                try:
                    self.ask_function(selected_media)
                except (IceFlix.Unauthorized, IceFlix.WrongMediaId) as e:
                    print(e)
                else:
                    continue
                
            elif option == "3":
                return 0 

    def name_searching(self):
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
        
        id_list = self._catalog_prx_.getTilesByName(title, full_title)

        if len(id_list) > 0:
            for id in id_list:
                try:
                    media_list.append(self._catalog_prx_.getTile(id))
                except(IceFlix.WrongMediaId, IceFlix.TemporaryUnavailable) as e:
                    print(e)
        else:
            return []
                        
        return media_list

    def tag_searching(self):
        media_list = []
        tag_list = self.ask_for_tags()
        
        if not tag_list:
            return -1

        option = input("¿Quieres que tu búsqueda coincida con todas tus etiquetas? (s/n): ")
        while option != "s" and option != "n":
            option = input("Inserta una opción válida: ")

        all_tags = None
        if option == "s":
            all_tags = True
        elif option == "n":
            all_tags = False

        try:
            id_list = self._catalog_prx_.getTilesByTags(tag_list, all_tags, self._user_token_)
        except IceFlix.Unauthorized:
            print(IceFlix.Unauthorized)
            return 0

        if len(id_list) > 0:
            for id in id_list:
                try:
                    media_list.append(self._catalog_prx_.getTile(id))
                except(IceFlix.WrongMediaId, IceFlix.TemporaryUnavailable) as e:
                    print(e)
        else:
            return -1

        return media_list

    def ask_for_tags(self):
        tag_list = []
        print("Inserta sus etiquetas. Para salir, dejar en blanco:")

        while 1:
            tag = input("Etiqueta: ")
            if tag == "":
                break
            tag_list.append(tag)
            
        return tag_list

    def select_media(self, media_list):
        counter = 0
        print("Videos encontrados:\n")
        for media in media_list:
            counter += 1
            print(str(counter) + ". " + path.split(media.info.name)[1])

        option = input("Selecciona un video o deja en blanco para salir: ")
        while option.isdigit() == False or int(option) < 1 or int(option) > counter:
            if option == "":
                return -1
            option = input("Inserta una opción válida: ")        

        selected_media = media_list[int(option)-1]
        return selected_media

    def ask_function(self, media_object):
        print("1. Reproducir")
        print("2. Añadir etiquetas")
        print("3. Eliminar etiquetas")
        print("4. Renombra título")
        print("5. Eliminar video")
        
        option = input(self.create_prompt("CatalogService"))
        while option.isdigit() == False or int(option) < 1 or int(option) > 5:
            option = input("Inserta una opción válida: ")
            
        if option == "1":
            try:
                video = self.play_video(media_object)
            except (IceFlix.Unauthorized, IceFlix.WrongMediaId) as e:
                print(e)
                input("Presiona Enter para continuar...")
            else:
                if video == 1:
                    print("No autorizado")
                    input("Pulsa enter para continuar...")
            
        elif option == "2":
            try:
                self.add_tags(media_object)
            except (IceFlix.Unauthorized, IceFlix.WrongMediaId) as e:
                print(e)
                input("Presiona Enter para continuar...")
            
        elif option == "3":
            try:
                self.remove_tags(media_object)
            except (IceFlix.Unauthorized, IceFlix.WrongMediaId) as e:
                print(e)
                input("Presiona Enter para continuar...")

        elif option == "4":
            try:
                self.rename_title(media_object)
            except (IceFlix.Unauthorized, IceFlix.WrongMediaId) as e:
                print(e)
                input("Presiona Enter para continuar...")
            print("Título renombrado correctamente")
            input("Presiona Enter para continuar...")

        elif option == "5":
            if not self._stream_provider_prx_:
                self.connect_stream_provider()
            try:
                self._stream_provider_prx_.deleteMedia(media_object.mediaId)
            except (IceFlix.Unauthorized, IceFlix.WrongMediaId) as e:
                print(e)
                input("Presiona Enter para continuar...")
            print("Video borrado correctamente")
            input("Presiona Enter para continuar...")

    def play_video(self, media):
        #media.provider = IceFlix.StreamProviderPrx.checkedCast(media.provider)
        if not self._stream_provider_prx_:
            try:
                self._stream_provider_prx_ = media.provider.getStream(media.mediaId, self._user_token_)
            except (IceFlix.Unauthorized, IceFlix.WrongMediaId) as e:
                print(IceFlix.Unauthorized)

        #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #sock.bind(("", 9998))
        try:
            config_url = self._stream_provider_prx_.getSDP(self._user_token_, 9998)
            print(config_url)
            print("Exito en el controller")
        except IceFlix.Unauthorized:
            print("Usuario no autorizado")
            return 1
        else:
            player = iceflixrtsp.RTSPPlayer()
            player.play(config_url)
            print("Introduce q para parar o presiona enter para seguir navegando")
            key = input()
            if key == "":
                return 0
            elif key == "q":
                _stream_provider_prx_.stop()
                player.stop()
                #sock.close()
                return 0

    def add_tags(self, media_object):
        tags_list = self.ask_for_tags()
        try:
            self._catalog_prx_.addTags(media_object.mediaId, tags_list, self._user_token_)
        except (IceFlix.Unauthorized, IceFlix.WrongMediaId) as e:
            print(e)
            raise e
        else:
            print("Etiquetas añadidas correctamente")
            input("Pulsa enter para continuar...")          
        
        return 0 
    
    def remove_tags(self, media_object):
        tags_list = self.ask_for_tags()
        try:
            self._catalog_prx_.removeTags(media_object.mediaId, tags_list, self._user_token_)
        except (IceFlix.Unauthorized, IceFlix.WrongMediaId) as e:
            print(e)
            raise e
        else:
            print("Etiquetas eliminadas correctamente")
            input("Pulsa enter para continuar...")
        return 0

    def rename_title(self, media_object):
        new_name = input("Nuevo nombre: ")
        self._catalog_prx_.renameTile(media_object.mediaId, new_name, self._admin_token_)

    def connect_stream_provider(self):
        stream_provider_proxy = input("Introduce el proxy del stream provider: ")
        proxy = self.communicator().stringToProxy(stream_provider_proxy)
        stream_provider_connection = IceFlix.StreamProviderPrx.checkedCast(proxy)
        try:
            check = stream_provider_connection.ice_ping()
        except Ice.ConnectionRefusedException:
            print("No ha sido posible conectar con Stream Provider")
        self._stream_provider_prx_ = stream_provider_connection

    def authenticator_service(self):
        ''' Gestiona el comando "authenticator" '''
        # MENU PARA ELEGIR LAS DISTINTAS BUSQUEDAS

        while 1:
            system("clear")
            self.format_prompt()
            print("1. Añadir usuario")
            print("2. Eliminar usuario")
            print("3. Salir")

            option = input(self.create_prompt("AuthenticatorService"))
            while option.isdigit() == False or int(option) < 1 or int(option) > 3:
                option = input("Inserta una opción válida: ")

            if option == "1":
                new_user = input("Introduce el nuevo nombre de usuario: ")
                new_password = getpass.getpass("Nueva Password: ")
                new_hash_password = hashlib.sha256(new_password.encode()).hexdigest()
                try:
                    self._auth_prx_.addUser(new_user, new_hash_password, self._admin_token_)
                except IceFlix.Unauthorized:
                    print(IceFlix.Unauthorized)
                    input()
                continue
            
            elif option == "2":
                delete_user = input("Introduce un usuario válido para eliminarlo: ")
                try:
                   self._auth_prx_.removeUser(delete_user, self._admin_token_)
                except IceFlix.Unauthorized:
                    print(IceFlix.Unauthorized)
                continue
            
            elif option == "3":
                return 0

    def stream_provider_service(self):
         while 1:
            system("clear")
            self.format_prompt()
            print("Opciones disponibles:")
            print("1. Subir un video")
            print("2. Volver\n")
            
            option = input(self.create_prompt("StreamProviderService"))
            while option.isdigit() == False or int(option) < 1 or int(option) > 3:
                option = input("Inserta una opción válida: ")

            if option == "1":
                self.connect_stream_provider()
                filename = input("Escribe el nombre del video que quieres subir: ")
                file = path.join(path.dirname(__file__), "local/" + filename)
                uploader = MediaUploaderI(file)
                adapter = self.communicator().createObjectAdapterWithEndpoints('MediaUploaderAdapter', 'tcp -p 9100')
                uploader_proxy = adapter.add(uploader, self.communicator().stringToIdentity('MediaUploader'))
                uploader_connection = IceFlix.MediaUploaderPrx.checkedCast(uploader_proxy)
                adapter.activate()
                uploader_connection.ice_ping()
                try:
                    file_id = self._stream_provider_prx_.uploadMedia(file, uploader_connection, self._admin_token_)
                    uploader_connection.close()
                    adapter.destroy()
                except (IceFlix.Unauthorized, IceFlix.UploadError) as e:
                    raise e
            
            elif option == "2":
                return 0

    def main_menu(self):
        while 1:
            system("clear")
            self.format_prompt()
            print("Opciones disponibles: ")
            print("1. Introducir token de administración")
            print("2. Login")
            print("3. Logout")
            print("4. Servicio de Catálogo")
            print("5. Servicio de Autenticación")
            print("6. Servicio de Streaming")
            print("7. Salir del cliente\n")

            option = input(self.create_prompt("MainService"))
                    
            while option.isdigit() == False or int(option) < 1 or int(option) > 7:
                if option == "":
                    option = input("IceFlix_MainService> ")
                else:
                    option = input("Inserta una opción válida: ")

            if option == "1":
                self.get_admin_token()
            elif option == "2":
                self.login()
            elif option == "3":
                self.logout()
            elif option == "4":
                self.catalog_service()
            elif option == "5":
                self.authenticator_service()
            elif option == "6":
                self.stream_provider_service()
            elif option == "7":
                print("Gracias por usar la aplicación uwu")
                sys.exit(1)
    
    def run(self, args):
        self.format_prompt()
        self.set_main_proxy()
        self.main_menu()
    
if __name__ == "__main__":
    sys.exit(Cliente().main(sys.argv))
        