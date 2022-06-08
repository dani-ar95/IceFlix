'''
Class to handle IceStorm objects
'''

import logging

import IceStorm

from constants import ICESTORM_PROXY_PROPERTY


class IceEventsError(Exception):
    '''This exception is raised in case of IceEvents error'''
    def __init__(self, msg='unknown error'):
        self._msg_ = msg
    
    def __str__(self):
        return 'IceStorm helper error: {}'.format(self._msg_)


class IceEvents:
    '''Handle Subscribers/Publishers objects easily'''
    def __init__(self, broker, property_name=ICESTORM_PROXY_PROPERTY):
        self._communicator_ = broker
        self._property_name_ = property_name
        self._topic_manager_ = None

    @property
    def topic_manager(self):
        '''Reference to IceStorm::TopicManager'''
        if not self._topic_manager_:
            proxy = self._communicator_.propertyToProxy(self._property_name_)
            print(proxy)
            if proxy is None:
                logging.error('Property "{}" results in a null proxy'.format(self._property_name_))
                raise IceEventsError('Missing property: {}'.format(self._property_name_))
            self._topic_manager_ = IceStorm.TopicManagerPrx.checkedCast(proxy)
        return self._topic_manager_

    def communicator(self):
        '''Get Ice::Communicator()'''
        return self._communicator_

    def get_topic(self, name):
        '''Get IceStorm::Topic object'''
        try:
            topic = self.topic_manager.retrieve(name)
        except IceStorm.NoSuchTopic:
            logging.warning('IceStorm::Topic({}) not found!'.format(name))
            topic = self.topic_manager.create(name)
        return topic

    def get_publisher(self, topic_name):
        '''Get IceStorm::Publisher object'''
        topic = self.get_topic(topic_name)
        return topic.getPublisher()

    def subscribe(self, topic_name, proxy):
        '''Subscribe object to a given IceStorm::Topic object'''
        topic = self.get_topic(topic_name)
        topic.subscribeAndGetPublisher({}, proxy)

    def unsubscribe(self, topic_name, proxy):
        '''Unsubscribe object from a given IceStorm::Topic object'''
        topic = self.get_topic(topic_name)
        topic.unsubscribe(proxy)
