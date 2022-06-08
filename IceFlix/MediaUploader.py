#!/usr/bin/python3
# pylint: disable=invalid-name

''' Clase contenedora de archivos para poder subirlos al servidor '''

import sys
from os import path
import Ice

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")
Ice.loadSlice(SLICE_PATH)
import IceFlix # pylint: disable=wrong-import-position


class MediaUploaderI(IceFlix.MediaUploader): # pylint: disable=inherit-non-class
    ''' Insntancia de MediaUploader'''

    def __init__(self, file_name):
        try:
            self._fd_ = open(file_name, "rb") # pylint: disable=bad-option-value,consider-using-with
        except FileNotFoundError:
            self._fd_ = None
            print("Archivo no encontrado: " + str(file_name))

    def receive(self, size: int, current=None): # pylint: disable=unused-argument
        ''' Retorna la cantidad indicada del fichero que contiene '''

        if self._fd_:
            chunk = self._fd_.read(size)
            return chunk

    def close(self, current=None): # pylint: disable=unused-argument
        ''' Cierra el descriptor del archivo que contiene '''

        if self._fd_:
            self._fd_.close()

    def share_data_with(self, service):
        """Share the current database with an incoming service."""
        service.updateDB(None, self.service_id)

    def updateDB(
        self, values, service_id, current
    ):  # pylint: disable=invalid-name,unused-argument
        """Receives the current main service database from a peer."""
        print(
            "Receiving remote data base from %s to %s", service_id, self.service_id
        )

class MediaUploaderServer(Ice.Application):
    ''' Servidor de Media Uploader '''

    def setup_announcements(self):
        """Configure the announcements sender and listener."""

        communicator = self.communicator()
        topic_manager = IceStorm.TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager")
        )

        try:
            topic = topic_manager.create("ServiceAnnouncements")
        except IceStorm.TopicExists:
            topic = topic_manager.retrieve("ServiceAnnouncements")

        self.announcer = ServiceAnnouncementsSender(
            topic,
            self.servant.service_id,
            self.proxy,
        )

        self.subscriber = ServiceAnnouncementsListener(
            self.servant, self.servant.service_id, IceFlix.StreamControllerPrx
        )

        subscriber_prx = self.adapter.addWithUUID(self.subscriber)
        topic.subscribeAndGetPublisher({}, subscriber_prx)

    def run(self, args):
        #sleep(1)

        broker = self.communicator()
        self.servant = MediaUploaderI()

        self.adapter = broker.createObjectAdapterWithEndpoints('MediaUploaderAdapter', 'tcp')
        media_uploader_proxy = self.adapter.addWithUUID(self.servant)

        self.proxy = media_uploader_proxy
        self.adapter.activate()
        self.setup_announcements()
        
        self.announcer.start_service()

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        self.announcer.stop()

if __name__ == "__main__":
    sys.exit(MediaUploaderServer().main(sys.argv))
