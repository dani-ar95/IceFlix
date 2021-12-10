#!/usr/bin/python3
import sqlite3
import IceFlix
import sys
import json
import Ice
from time import sleep
from os import path

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")
DB_PATH = path.join(path.dirname(__file__), "media.db")
Ice.loadSlice(SLICE_PATH)

class MediaCatalogI(IceFlix.MediaCatalog):
    
    def __init__(self):
        self._media_ = dict()
        # Obtener medios de la base de datos
        

    def getTile(self, mediaId: str, current=None):
        ''' Retorna un objeto Media con la informacion del medio con el ID dado '''
        media = self._media_.get(mediaId)
        if media:
            return media
    
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        print(mediaId)
        c.execute("SELECT * FROM media WHERE id LIKE '{}'".format(mediaId))

        query = c.fetchall()

        # Buscar el ID en bbdd y temporal
        if not query and mediaId not in self._media_.keys():
            raise IceFlix.WrongMediaId

        # Buscar provider en temporal
        provider = self._media_.get(mediaId).provider
        if provider:
            try:
                provider.ice_ping()
            except Ice.ConnectionRefusedException:
                raise IceFlix.TemporaryUnavailable
            else:
                return self._media_.get(mediaId)
        else:
            # Buscar provider en bbdd
            try:
                provider = current.adapter.getCommunicator(
                ).stringToProxy(query[0][3])
            except Ice.NoEndpointException:
                raise IceFlix.TemporaryUnavailable

        name = query.pop(0)
        tags = []
        while(query):
            tags.append(query.pop(0))

        info = IceFlix.MediaInfo(name, tags)
        media_obj = IceFlix.Media(mediaId, provider, info)
        conn.close()
        return media_obj

    def getTilesByName(self, name, exact: bool, current=None):
        ''' Retorna una lista de IDs a partir del nombre dado'''

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        id_list = []

        # Buscar por nombre en la BBDD
        if exact:
            c.execute("SELECT id FROM media WHERE name LIKE'{}'".format(name))
        else:
            c.execute(
                "SELECT id FROM media WHERE LOWER(name) LIKE LOWER('%{}%')".format(name))

        list_returned = c.fetchall() # Ejecuta la query
        conn.close()

        if list_returned: # Si la query devuelve algo, añadirlo al resultado
            for media in list_returned: # La query devuelve una lista por cada medio, cada lista tiene (id, tag, name, proxy)
                id_list.append(media[0])

        # Buscar por nombre en los medios dinámicos
        if exact:
            for media in self._media_.values():
                if name == media.info.name:
                    id_list.append(media.mediaId)
        else:
            for media in self._media_.values():
                if name in media.info.name:
                    id_list.append(media.mediaId)

        return id_list


    def getTilesByTags(self, tags: list, includeAllTags: bool, userToken, current=None):
        ''' Retorna una lista de IDs de los medios con las tags dadas '''

        try:
            username = self.check_user_name(userToken)
        except (IceFlix.Unauthorized, IceFlix.TemporaryUnavailable) as e:
            raise IceFlix.Unauthorized
        else:

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            id_list = []

            # Buscar IDs en persistente
            c.execute("SELECT id FROM media ") # Revisar si funciona cambiando el orden de las tags en la busqueda

            list_returned = c.fetchall() # Ejecuta la query
            conn.close()

            with open("users.json", "r") as f:
                obj = json.load(f)
                for i in obj["users"]:
                    if i["name"] == username:
                        user_tags = i["tags"]

            if includeAllTags:
                for media_id in list_returned:
                    id_tags = user_tags.get(media_id)
                    valid = bool(x for x in tags in id_tags)
                    if valid: 
                        id_list.append(media_id)
            else:
                for media_id in list_returned:
                    id_tags = user_tags.get(media_id)
                    for x in id_tags:
                        if x in tags:
                            valid = True
                            break
                    if valid:
                        id_list.append(media_id)
            

            # Buscar por tags en medios dinámicos
            valid = False
            if includeAllTags:
                for media in self._media_.values():
                    if media.mediaId in user_tags.keys():
                        user_tags_for_media = user_tags.get(media.mediaId)
                        valid = bool(x for x in user_tags_for_media in tags)
                        if valid and media.mediaId not in id_list:
                            id_list.append(media.mediaId)
            else:
                for media in self._media_.values():
                    if media.mediaId in user_tags.keys():
                        user_tags_for_media = user_tags.get(media.mediaId)
                        for tag in user_tags_for_media:
                            if tag in tags:
                                valid = True
                                break
                        if valid and media.mediaId not in id_list:
                            id_list.append(media.mediaId)

            return id_list

    def addTags(self, mediaId: str, tags: list, userToken, current=None):
        ''' Añade las tags dadas al medio con el ID dado '''

        try:
            user_name = self.check_user_name(userToken)
        except (IceFlix.Unauthorized, IceFlix.TemporaryUnavailable) as e:
            raise IceFlix.Unauthorized

        else:
            if mediaId not in self._media_.keys():
                raise IceFlix.WrongMediaId

            # Cambiar tags persistentes
            with open("users.json", "r") as f:
                obj = json.load(f)

            for i in obj["users"]:
                if i["user"] == user_name:
                    i.update({mediaId: tags})
                    break

            with open('users.json', 'w') as file:
                json.dump(obj, file, indent=2)

            # Cambiar tags de medios dinámicos, creo que no hace falta
            for media in self._media_.values():
                if media.mediaID == mediaId:
                    media.info.tags.append([tag for tag in tags if tag not in media.info.tags]) # Añade las tags que no tiene

            return 0 # ¿Deberíamos usar los EXIT_OK y eso?

    def removeTags(self, mediaId: str, tags: list,  userToken, current=None):
        ''' Elimina las tags dadas del medio con el ID dado '''

        try:
            user_name = self.check_admin(userToken)
        except (IceFlix.Unauthorized, IceFlix.TemporaryUnavailable) as e:
            raise IceFlix.Unauthorized
        else:

            # Cambiar tags persistentes
            with open("users.json", "r") as f:
                obj = json.load(f)

            for i in obj["users"]:
                if i["user"] == user_name:
                    user_tags = i["tags"]
                    if mediaId in user_tags.values():
                        lista_de_tags_del_medio = user_tags.get(mediaId)
                        new_list = [x for x in lista_de_tags_del_medio if x not in tags]
                        user_tags.update({mediaId: new_list})

            with open('users.json', 'w') as file:
                json.dump(obj, file, indent=2)
                
            return 0

            

    def renameTile(self, mediaId, name, adminToken, current=None):
        ''' Renombra el medio de la estructura correspondiente '''

        try:
            self.check_admin(adminToken)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized
        else:    

            # Buscar id en medios estáticos
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                "SELECT * FROM media where id LIKE '{}'".format(mediaId))
            media = conn.commit()
            conn.close()
            
            # Buscar id en medios dinamicos
            if mediaId not in self._media_.keys() and not media:
                raise IceFlix.WrongMediaId

            # Cambiar media en medios dinamicos
            if mediaId in self._media_.keys():
                medio = self._media_.get(mediaId)
                medio.info.name = name
                self._media_.update({mediaId: medio})

            # Buscar medio en bbdd
            try:
                in_ddbb = self.getTile(mediaId)
            except IceFlix.Unauthorized:
                raise IceFlix.Unauthorized

            else:
                if in_ddbb:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute(
                        "UPDATE media SET name = '{}' WHERE id LIKE '{}'".format(name, mediaId))
                    conn.commit()
                    conn.close()


    def updateMedia(self, mediaId, initialName, provider, current=None):
        ''' Añade o actualiza el medio del ID dado '''

        info = IceFlix.MediaInfo(initialName, [])
        nuevo = IceFlix.Media(mediaId, provider, info)
        self._media_.update({mediaId: nuevo})
        print("Añadido medio:")
        print({mediaId: nuevo})

    def check_admin(self, admin_token: str):
        ''' Comprueba si un token es Administrador '''

        try:
            is_admin = self._main_prx_.isAdmin(admin_token)
            if not is_admin:
                raise IceFlix.Unauthorized
        except IceFlix.TemporaryUnavailable:
            print("Se ha perdido conexión con el servidor Main")
            raise IceFlix.Unauthorized
        else:
            return is_admin

    def check_user(self, user_token: str):
        ''' Comprueba que la sesion del usuario es la actual '''

        try:
            auth_prx = self._main_prx_.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            raise IceFlix.TemporaryUnavailable
        else:
            try:
                user = auth_prx.isAuthorized(user_token)
            except IceFlix.Unauthorized as e:
                raise e
            return user

    def check_user_name(self, user_token: str):
        ''' Comprueba que la sesion del usuario es la actual '''
        try:
            auth_prx = self._main_prx_.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            raise IceFlix.TemporaryUnavailable
        else:
            try:
                user_name = auth_prx.whois(user_token)
            except IceFlix.Unauthorized as e:
                raise e
            return user_name

class MediaCatalogServer(Ice.Application):
    def run(self, argv):
        sleep(2)
        main_service_proxy = self.communicator().stringToProxy(argv[1])
        main_connection = IceFlix.MainPrx.checkedCast(main_service_proxy)
        if not main_connection:
            raise RuntimeError("Invalid proxy")

        broker = self.communicator()
        servant = MediaCatalogI()

        adapter = broker.createObjectAdapterWithEndpoints(
            'MediaCatalogAdapter', 'tcp -p 9092')
        media_catalog_proxy = adapter.add(
            servant, broker.stringToIdentity('MediaCatalog'))

        adapter.activate()

        main_connection.register(media_catalog_proxy)
        servant._main_prx_ = main_connection
        

        self.shutdownOnInterrupt()
        broker.waitForShutdown()


if __name__ == '__main__':
    # MediaCatalogServer().run(sys.argv)
    sys.exit(MediaCatalogServer().main(sys.argv))
