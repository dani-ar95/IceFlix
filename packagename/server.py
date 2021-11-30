import os
import Ice
import IceFlix
import binascii
import logging
import glob



class RemoteFileSystem(FileTransfer.RemoteFileSystem):
    def __init__(self, root_folder):
        logging.info(f'serving directory ...')
        candidates = glob.glob(os.path.join(root_folder, '*'), recursive=True)
        prefix_len = len(root_folder) + 1
        self, _root_ = root_folder
        self, _files_ = [filename[prefix_len:] for filename in candidates]
        logging.debug("list of files : %s",self.__files__)
        
    def list(self, current=None):
        logging.debug("clinet asked for lsit")
        return self._files_
    
    def open(self, filename, current=None):
        if filename not in self.__files__:
            raise FileTransfer.FileNotFound(filename)
        target = os.path.join(self._root_, filename)
        servant = RemoteFile(target)
        proxy = current.adapter.addWithUUID(servant)
        return FileTransfer.RemoteFilePrx.checkedCast(proxy)
    
    
class RemoteFile(FileTransfer.RemoteFile):
    def __init__(self, filename):
        logging.debug("serving file...")
        self,_filename_ = filename
        self,_fd_ = open(filename, 'rb')
    
    def getSize(self, current = None):
        #asked for size of file...
        return Path(self._filename_).stat().st_size
    
    def receive(self, size, current = None):
        logging.debug("sending chunk of")
        chunk = self._fd_.read(size)
        data = binascii.b2a_base64(chunk, newline=False).decode(encoding='utf-8')
        return data
    
    def close(self, current = None):
        self._fd_.close()
        current.adapter.remove(current.id)


class Server(Ice.Application):
    def run(self, argv):
        argv.pop()
        root_fs = os.getcwd() if not argv else argv.pop()
        servant = RemoteFileSystem(root_fs)
        adapter = self.communicator().createObjectAdapterWithEndpoints("fsAdapter", "default -p 10000")
        proxy = adapter.add(servant, self.communicator().stringToIdentity("FileTransfer"))
        adapter.activate()
        
        self.shutdownOnInterrupt()
        self.communicator().waitForShutdown()