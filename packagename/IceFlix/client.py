#!/usr/bin/env python3

"""Implementación de un cliente de las interfaces RemoteFileSystem y RemoteFile."""

import os
import sys
import logging
import itertools

import Ice
Ice.loadSlice('filetransfer.ice')

import FileTransfer  # pylint: disable=import-error,wrong-import-position

EXIT_OK = 0
EXIT_ERROR = 1

CHUNK_SIZE = 4096
SPINNER = itertools.cycle(['|', '/', '-', '\\'])


class Client(Ice.Application):
    """Implementacion del cliente."""

    def run(self, args):
        """Método principal para la ejecución del cliente."""
        proxy = self.communicator().stringToProxy(args[1])
        file_system = FileTransfer.RemoteFileSystemPrx.checkedCast(proxy)
        if not file_system:
            logging.error('Provided proxy is not a RemoveFileSystem() object')
            return EXIT_ERROR

        print(' Available files')
        print('=================')

        print(" ", end="")
        print('\n '.join(file_system.list()))

        requested_file = input('\nEnter filename or empty for cancel: ')
        if not requested_file:
            print('Cancelled by user')
            return EXIT_OK

        try:
            remote_file = file_system.open(requested_file)

        except FileTransfer.FileNotFound:
            print('Requested file not found!')
            return EXIT_ERROR

        destination_filename = input('Destination filename: ')

        if os.path.exists(destination_filename):
            print("Cannot overwrite existing files")
            return EXIT_ERROR

        with open(destination_filename, 'wb') as out:
            count = 0
            filesize = remote_file.getSize()
            while True:
                chunk = remote_file.receive(CHUNK_SIZE)
                if not chunk:
                    break

                out.write(chunk)
                print(f'\r\033[KDownloading {count}/{filesize} bytes... {next(SPINNER)}', end='')
                count += len(chunk)

            print(f'\r\033[KDownloading {count}/{filesize} bytes... {next(SPINNER)}', end='')

        remote_file.close()
        print('\nTransfer completed!')
        return EXIT_OK


if __name__ == '__main__':
    sys.exit(Client().main(sys.argv))
