""" Modulo para debugear el topic ServiceAnnoucements """

from time import sleep
import os
import sys
import json
import secrets
import Ice
import IceStorm
import uuid
from Main import MainI

try:
    import IceFlix
except ImportError:
    Ice.loadSlice(os.path.join(os.path.dirname(__file__), "iceflix.ice"))
    import IceFlix

""" Clases para debuguear """

class ServiceAnnouncementsListener(IceFlix.ServiceAnnouncements):
    """Listener del topic ServiceAnnoucements"""

    def __init__(self, own_servant, own_service_id, own_type):
        """Initialize a ServiceAnnouncements topic listener """
        pass

    def newService(self, service, service_id, current):  # pylint: disable=invalid-name,unused-argument
        """Receive the announcement of a new started service."""

        print(f"[ServiceAnnoucements] NewService: Servicio: {service}, ID: {service_id}")


    def announce(self, service, service_id, current):  # pylint: disable=unused-argument
        """Receive an announcement."""

        print(f"[ServiceAnnoucements] Announce: Servicio: {service}, ID: {service_id}")


class ServiceAnnouncementsSender:
    """The instances send the announcement events periodically to the topic."""

    def __init__(self, topic, service_id, servant_proxy):
        """Initialize a ServiceAnnoucentsSender """
        pass

    def start_service(self):
        """Start sending the initial announcement."""
        pass
    def announce(self):
        """Start sending the announcements."""
        pass

    def stop(self):
        """Stop sending the announcements."""
        pass


""" Ejecutable """


class DebugAuthenticator(Ice.Application):
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

        self.announcer = ServiceAnnouncementsSender(topic, self.servant.service_id,
            self.proxy,
        )

        self.subscriber = ServiceAnnouncementsListener(self.servant, self.servant.service_id,
            IceFlix.AuthenticatorPrx
        )

        subscriber_prx = self.adapter.addWithUUID(self.subscriber)
        topic.subscribeAndGetPublisher({}, subscriber_prx)


    def run(self, argv):
        ''' Implementación del debug de ServiceAnnouncements '''

        broker = self.communicator()
        servant = MainI()
        properties = broker.getProperties()
        servant._token_ = properties.getProperty("AdminToken")

        self.adapter = broker.createObjectAdapter(self.subscriber)
        self.adapter.add(servant, broker.stringToIdentity("Main"))

        self.adapter.activate()

        self.setup_announcements()
        self.announcer.start_service()

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        self.announcer.stop()

        return 0

if __name__ == '__main__':
    sys.exit(DebugAuthenticator().main(sys.argv))