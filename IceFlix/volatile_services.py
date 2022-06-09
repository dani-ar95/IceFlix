import Ice # pylint: disable=import-error,wrong-import-position
from os import path

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")
Ice.loadSlice(SLICE_PATH)
import IceFlix # pylint: disable=import-error,wrong-import-position

class VolatileServices(IceFlix.VolatileServices):
    def __init__(self, auth_services, catalog_services, current=None):
        '''Inicializa el objeto.'''
        self.authenticators = auth_services
        self.mediaCatalogs = catalog_services # pylint: disable=invalid-name 
        
    def get_authenticators(self):
        return self.authenticators
    
    def get_catalogs(self):
        return self.mediaCatalogs


class UsersDB(IceFlix.UsersDB):
    def __init__(self, user_passwords, user_tokens, current=None):
        self.userPasswords = user_passwords
        self.usersToken = user_tokens

    def get_users_passwords(self):
        return self.userPasswords

    def get_users_tokens(self):
        return self.usersToken