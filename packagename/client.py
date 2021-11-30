import sys, Ice
import IceFlix
import binascii
import os

with Ice.initialize(sys.argv) as communicator:
    base = communicator.stringToProxy("StreamControllerID:default -p 10000")
    controller = IceFlix.StreamControllerPrx.checkedCast(base)
    if not controller:
        raise RuntimeError("Invalid proxy")

    #controller.getSDP("Echate un token bro", 20292)

class Client(Ice.Application):
    
    def run(self, argv):
        proxy = self.communicator.stringToProxy(argv[1])
        fileSystem = FileTransfer.RemoteFileSystemPrx.checkedCast(proxy)
        controller = IceFlix.StreamControllerPrx.checkedCast(base)
        if not fileSystem:
            raise RuntimeError("Invalid proxy")

        for filename in fileSystem.list():
            print(f'{filename}')
        print()
        requested_file = input('Enter the file name: ')
        #control requested_file
        
        try:
            fd = fileSystem.open(requested_file)
        except FileTransfer.FileNotFound:
            print("Req file not found")
            return EXIT_ERROR
        
        destination_filename = input("Dest filename: ")
        with open(destination_filename, 'wb') as out:
            count = 0
            filesize = fd.getSize()
            while True:
                data = fd.receive(CHUNK_SIZE)
                if not data:
                    break
                chunk = binascii.a2b_base64(data.encode(encoding='utf-8'))
                out.write(chunk)
                #print('\r\0) pollas
                count += len(chunk)
                if len(chunk) < CHUNK_SIZE:
                    break
        fd.close()
        print()
        return EXIT_OK    
        

       # controller.getSDP("Echate un token bro", 20292)