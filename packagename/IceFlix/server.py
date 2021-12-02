#!/usr/bin/env python3

"""Servidor de RemoteFile y RemoteFileSystem.

Implementación de los sirvientes de RemoteFile and RemoteFileSystem junto a
la instrumentación para ofrecerlos como servicio.
"""

import os
import sys
import glob
import logging
from pathlib import Path

import Ice

Ice.loadSlice('filetransfer.ice')
import FileTransfer  # pylint: disable=import-error,wrong-import-position


logging.basicConfig(level=logging.DEBUG)
EXIT_OK = 0


class RemoteFileSystem(FileTransfer.RemoteFileSystem):
    """Sirviente de RemoteFileSystem."""

    def __init__(self, root_folder):
        """Inicializador del sirviente."""
        logging.debug('Serving directory: %s', root_folder)
        candidates = glob.glob(os.path.join(root_folder, '*'), recursive=True)
        prefix_len = len(root_folder) + 1
        self._root_ = root_folder
        self._files_ = [filename[prefix_len:] for filename in candidates]

    def list(self, current=None):  # pylint: disable=unused-argument
        """Devuelve la lista de ficheros disponibles."""
        return self._files_

    def open(self, filename, current=None):
        """Factoría de objetos RemoteFile."""
        if filename not in self._files_:
            raise FileTransfer.FileNotFound(filename)
        target = os.path.join(self._root_, filename)
        servant = RemoteFile(target)
        proxy = current.adapter.addWithUUID(servant)
        return FileTransfer.RemoteFilePrx.checkedCast(proxy)


class RemoteFile(FileTransfer.RemoteFile):
    """Sirviente de RemoteFile."""

    def __init__(self, filename):
        """Inicializador del RemoteFile."""
        logging.debug('Serving file: %s', filename)
        self._filename_ = filename
        self._fd_ = open(filename, 'rb')  # pylint: disable=consider-using-with

    def getSize(self, current=None):  # pylint: disable=invalid-name,unused-argument
        """Devuelve el tamaño del fichero."""
        return Path(self._filename_).stat().st_size

    def receive(self, size, current=None):  # pylint: disable=unused-argument
        """Lee un bloque de tamaño `size` y lo devuelve."""
        chunk = self._fd_.read(size)
        return chunk

    def close(self, current=None):
        """Cierra el envío del fichero y elimina el objeto del adaptador."""
        self._fd_.close()
        current.adapter.remove(current.id)


class Server(Ice.Application):
    """Implementacion del servidor."""

    def run(self, args):
        """Entry point."""
        args.pop()
        root_fs = os.getcwd() if not args else args.pop()
        servant = RemoteFileSystem(root_fs)

        adapter = self.communicator().createObjectAdapterWithEndpoints("fsAdapter", "tcp -p 36000")
        proxy = adapter.add(servant, self.communicator().stringToIdentity('filesystem'))
        print(proxy, flush=True)
        adapter.activate()

        self.shutdownOnInterrupt()
        self.communicator().waitForShutdown()

        return EXIT_OK


if __name__ == '__main__':
    sys.exit(Server().main(sys.argv))
