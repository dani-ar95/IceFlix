#!/usr/bin/python3
import sqlite3
import IceFlix
import sys
import Ice
Ice.loadSlice("./iceflix.ice")


class MediaCatalogI(IceFlix.MediaCatalog):
    
    def __init__(self):
        self._media_ = dict()

    def getTile(self, mediaId: str, current=None):
        ''' Retorna un objeto Media con la informacion del medio con el ID dado '''

        conn = sqlite3.connect("./media.db")
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

        conn = sqlite3.connect("./media.db")
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
            self.check_user(userToken)
        except (IceFlix.Unauthorized, IceFlix.TemporaryUnavailable) as e:
            raise IceFlix.Unauthorized
        else:

            conn = sqlite3.connect("media.db")
            c = conn.cursor()
            id_list = []

            # Buscar por tags en BBDD
            if includeAllTags:
                c.execute("SELECT id FROM media WHERE tags LIKE {}".format(tags)) # Revisar si funciona cambiando el orden de las tags en la busqueda
            else:
                c.execute("SELECT id FROM media WHERE tags IN {}".format(tags))

            list_returned = c.fetchall() # Ejecuta la query
            conn.close()
            
            if list_returned: # Si la query devuelve algo, añadirlo al resultado
                id_list.append([id for id in list_returned])

            # Buscar por tags en medios dinámicos
            if includeAllTags:
                for media in self._media_.values():
                    media_tags = [tag for tag in media.info.tags] # Sacar todos los tags de un medio
                    if media_tags == tags:                        # Comprobar con los tags que nos piden (no se si funciona cambiando el orden)
                        id_list.append(media.mediaId)
            else:
                for media in self._media_.values():
                    media_tags = [tag for tag in media.info.tags] # Comprobar que las tags que nos piden estan contenidas en todas las del medio
                    if tags in media_tags:
                        id_list.append(media.mediaId)

            return id_list

    def addTags(self, mediaId: str, tags: list, userToken, current=None):
        ''' Añade las tags dadas al medio con el ID dado '''

        try:
            self.check_user(userToken)
        except (IceFlix.Unauthorized, IceFlix.TemporaryUnavailable) as e:
            raise IceFlix.Unauthorized

        else:
            if mediaId not in self._media_.keys():
                raise IceFlix.WrongMediaId

            conn = sqlite3.connect("media.db")
            c = conn.cursor()

            # Cambiar tags del medio en la BBDD
            c.execute("SELECT tags FROM media WHERE id LIKE ''".format(id)) # Pedir las tags actuales del medio
            current_tags = c.fetchall() # Ejecuta la query
            new_tags = [current_tags.append([tag for tag in tags if tag not in current_tags])] # Añade las tags que no tiene
            c.execute("UPDATE media SET tags = '{}' WHERE id = '{}'".format(new_tags, mediaId)) # ¿Esto se añade como lista? ¿O como tags individuales?
            conn.commit()
            conn.close()

            # Cambiar tags de medios dinámicos
            for media in self._media_.values():
                if media.mediaID == mediaId:
                    media.info.tags.append([tag for tag in tags if tag not in media.info.tags]) # Añade las tags que no tiene

            return 0 # ¿Deberíamos usar los EXIT_OK y eso?

    def removeTags(self, mediaId: str, tags: list,  userToken, current=None):
        ''' Elimina las tags dadas del medio con el ID dado '''

        try:
            self.check_admin(userToken)
        except (IceFlix.Unauthorized, IceFlix.TemporaryUnavailable) as e:
            raise IceFlix.Unauthorized
        else:

            if mediaId not in self._media_.keys():
                raise IceFlix.WrongMediaId

            conn = sqlite3.connect("media.db")
            c = conn.cursor()

            # Quitar tags de medios en la BBDD
            c.execute("SELECT tags FROM media WHERE id LIKE ''".format(id))
            current_tags = c.fetchall() # Ejecuta la query
            new_tags = [x for x in current_tags if x not in tags] # Elimina las tags indicadas
            c.execute("UPDATE media SET tags = '{}' WHERE id = '{}'".format(
                tags.append(new_tags), mediaId))
            conn.commit()
            conn.close()

            # Falta hacerlo en los medios dinámicos

    def renameTile(self, id, name, adminToken, current=None):
        ''' Renombra el medio de la estructura correspondiente '''

        try:
            self.check_admin(adminToken)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized

        if id not in self._media_.keys():
            raise IceFlix.WrongMediaId

        else:
            try:
                in_ddbb = self.getTitle(id)
            except IceFlix.Unauthorized:
                raise IceFlix.Unauthorized

            if in_ddbb:
                conn = sqlite3.connect("media.db")
                c = conn.cursor()
                c.execute(
                    "UPDATE media SET name = '{}' WHERE id = '{}'".format(name, id))
                conn.commit()
                conn.close()

            media = self._media_.get(id)
            media.info.name = name
            self._media_.update(id, media)

    def updateMedia(self, id, initialName, provider, current=None):
        ''' Añade o actualiza el medio del ID dado '''

        info = IceFlix.MediaInfo(initialName, ["tag"])
        nuevo = IceFlix.Media(id, provider, info)
        self._media_.update({id: nuevo})
        print("Añadido medio:")
        print({id: nuevo})

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
            auth_prx = MediaCatalogServer.main_connection.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            raise IceFlix.TemporaryUnavailable
        else:
            try:
                user = auth_prx.isAuthorized(user_token)
            except IceFlix.Unauthorized as e:
                raise e


class MediaCatalogServer(Ice.Application):
    def run(self, argv):
        # sleep(1)
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
