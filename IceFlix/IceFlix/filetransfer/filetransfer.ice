//
// Example of file transfer service
//
module FileTransfer {

    // Raised if provided filename not found
    exception FileNotFound { string filename; };

    // List of strings
    sequence<string> StringList;

    // Sequence of bytes
    sequence<byte> Bytes;

    // Handle downloading
    interface RemoteFile {
        int getSize();
        Bytes receive(int size);
        void close();
    };

    // File server
    interface RemoteFileSystem {
        RemoteFile* open(string filename) throws FileNotFound;        
        StringList list();
    };

};
