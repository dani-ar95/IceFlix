import sys, Ice
Ice.loadSlice("IceFlix.ice")
import IceFlix

class MediaCatalogI(IceFlix.MediaCatalog):
    
    def __init__(self, argv):
        pass

    def getTitle(self, id, current=None):
        # Código
        # Throws WrongMediaID, Temporaryunavailable
        # Retorna objeto tipo Media
        pass

    def getTitlesByName(self, name, exact: bool, current=None):
        # Código
        # Retorna objeto tipo StringList
        pass

    def getTitlesByTags(self, tags, includeAllTags: bool, userToken, current=None):
        # Código
        # Throws Unauthorized, WrongMediaID
        # Retorna objeto tipo StringList
        pass

    def addTags(self, id, tags, userToken, current=None):
        # Código
        # Throws Unauthorized, WrongMediaID
        pass

    def removeTags(self, id, name, adminToken, current=None):
        # Código
        # Throws Unauthorized, WrongMediaID
        pass

    def renameTitle(self, id, name, adminToken, current=None):
        # Cödigo
        # Throws Unauthorized, WrongMediaID
        pass

    def updateMedia(self, id, initialName, provider):
        # Código
        # Throws Unauthorized, WrongMediaID
        pass

with Ice.initialize(sys.argv) as communicator:
    adapter = communicator.createObjectAdapterWithEndpoints("MediaCatalog", "default -p 10000")
    object = MediaCatalogI()
    adapter.add(object, communicator.stringToIdentity("MediaCatalogID"))
    adapter.activate()
    communicator.waitForShutdown()