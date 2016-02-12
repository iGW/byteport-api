import json

from client_base import *

try:
    from stompest.config import StompConfig
    from stompest.protocol import StompSpec
    from stompest.sync import Stomp
    from stompest.error import StompConnectionError
except ImportError:
    print "Could not import Stompest library. The STOMP client will not be supported."
    print ""
    print "If you need to use that client, please do:"
    print "pip install stompest"

import time

class ByteportStompClient(AbstractByteportClient):
    DEFAULT_BROKER_HOSTS = ['broker.igw.se', 'broker1.igw.se', 'broker2.igw.se', 'broker3.igw.se']
    QUEUE_NAME = '/queue/simple_string_dev_message'

    client = None

    def __init__(self, namespace, login, passcode, broker_hosts=DEFAULT_BROKER_HOSTS):

        self.namespace = str(namespace)

        for broker_host in broker_hosts:
            broker_url = 'tcp://%s:61613' % broker_host
            self.CONFIG = StompConfig(broker_url, version=StompSpec.VERSION_1_2)
            self.client = Stomp(self.CONFIG)

            try:
                # Convention: set vhost to the namespace. This will require a message-boss consuming on this vhost!!!
                vhost = namespace
                self.client.connect(headers={'login': login, 'passcode': passcode}, host=vhost)
                print "Connected to %s using protocol version %s" % (broker_host, self.client.session.version)
            except StompConnectionError:
                pass

    def disconnect(self):
        self.client.disconnect()

    def __send_json_message(self, json):
        self.client.send(self.QUEUE_NAME, json)

    def __send_message(self, uid, data_string, timestamp=None):

        if timestamp:
            timestamp = self.auto_timestamp(timestamp)
        else:
            timestamp = int(time.time())

        message = dict()
        message['uid'] = str(uid)
        message['namespace'] = self.namespace
        message['data'] = str(data_string)
        message['timestamp'] = str(timestamp)

        self.__send_json_message(json.dumps([message]))

    def store(self, data=None, device_uid=None, timestamp=None):
        if type(data) != dict:
            raise ByteportClientException("Data must be of type dict")

        for key in data.keys():
            self.verify_field_name(key)

        delimited_data = ';'.join("%s=%s" % (key, self.utf8_encode_value(val)) for (key, val) in data.iteritems())

        self.__send_message(device_uid, delimited_data, timestamp)

