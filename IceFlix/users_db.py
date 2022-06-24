''' Módulo para manejar los datos de los usuarios '''

import os
import Ice # pylint: disable=import-error,wrong-import-position

try:
    import IceFlix
except ImportError:
    Ice.loadSlice(os.path.join(os.path.dirname(__file__), "iceflix.ice"))
    import IceFlix # pylint: disable=import-error,wrong-import-position

class UsersDB(IceFlix.UsersDB):
    ''' Clase para el objeto UsersDB'''
    def __init__(self, user_passwords, user_tokens, current=None): #pylint: disable=unused-argument
        self.userPasswords = user_passwords # pylint: disable=invalid-name
        self.usersToken = user_tokens # pylint: disable=invalid-name

    def get_users_passwords(self):
        ''' Retorna la lista de contraseñas '''
        return self.userPasswords

    def get_users_tokens(self):
        ''' Retorna la lista de tokens '''
        return self.usersToken
