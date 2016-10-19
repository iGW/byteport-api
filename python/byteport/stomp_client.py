import json
import logging

from client_base import *


try:
    from stompest.config import StompConfig
    from stompest.protocol import StompSpec
    from stompest.sync import Stomp
    from stompest.error import StompConnectionError, StompProtocolError
except ImportError:
    print "Could not import Stompest library. The STOMP client will not be supported."
    print ""
    print "If you need to use that client, please do:"
    print "pip install stompest"

import time


class ByteportStompClient(AbstractByteportClient):
    DEFAULT_BROKER_HOST = 'stomp.byteport.se'
    STORE_QUEUE_NAME = '/queue/simple_string_dev_message'

    SUPPORTED_CHANNEL_TYPES = ['topic', 'queue']

    client = None

    def __init__(self, namespace, login, passcode, broker_host=DEFAULT_BROKER_HOST, device_uid=None, channel_type='topic', channel_key=''):
        '''
        Create a ByteportStompClient. This is a thin wrapper to the underlying STOMP-client that connets to the Byteport Broker

        If a device_uid is given, a subscription will be made for Messages sent through Byteport.

        The channel_type must be either 'topic' or 'queue'. Set top topic if unsure on what to use (use queue if you need to
        use multiple consumers for a single device, this is not how most applications are set up).

        If on Byteport 1.5, you can supply a channel_key. The channel key is default set to the namespace API key (which is shared
        among all devices), but can be overridden per device from the Byteport Device Manager, you could set it to the Device Key
        or any other randomly set key (see the Byteport web for how to do this).

        :param namespace:
        :param login:           Broker username (Byteport web users are _not_ valid broker users). Ask support@byteport.se for access.
        :param passcode:        Broker passcode
        :param broker_hosts:    [optional] A list of brokers to connect to
        :param device_uid:      [optional] The device UID to subscribe for messages on
        :param channel_type:    [optional] Defaults to queue.
        :param channel_key:     [optional] Must match the configured key in the Byteport Device Manager

        '''

        self.namespace = str(namespace)
        self.device_uid = device_uid

        if channel_type not in self.SUPPORTED_CHANNEL_TYPES:
            raise Exception("Unsupported channel type: %s" % channel_type)

        broker_url = 'tcp://%s:61613' % broker_host
        self.CONFIG = StompConfig(broker_url, version=StompSpec.VERSION_1_2)
        self.client = Stomp(self.CONFIG)

        try:
            self.client.connect(headers={'login': login, 'passcode': passcode}, host='/')
            logging.info("Connected to Stomp broker at %s using protocol version %s" % (broker_host, self.client.session.version))

            # Set up a subscription on the correct queue if a Specific device UID was given
            if self.device_uid:
                subscribe_headers = dict()
                subscribe_headers[StompSpec.ACK_HEADER] = StompSpec.ACK_CLIENT_INDIVIDUAL
                subscribe_headers[StompSpec.ID_HEADER] = '0'

                device_message_queue_name = '/%s/device_messages%s_%s.%s' % (channel_type, channel_key, namespace, device_uid)

                self.subscription_token = self.client.subscribe(device_message_queue_name, subscribe_headers)
                logging.info("Subscribing to channel %s" % device_message_queue_name)
        except StompProtocolError as e:
            logging.error("Client socket connected, but probably failed to login. (ProtocolError)")
            raise

        except StompConnectionError:
            logging.error("Failed to connect to Stomp Broker at %s" % broker_host)
            raise

    def disconnect(self):
        if self.subscription_token:
            try:
                self.client.unsubscribe(self.subscription_token)
            except Exception as e:
                logging.error(u'Unsubscribe failed, reason %s' % e)

        self.client.disconnect()

    def __send_json_message(self, json):
        self.client.send(self.STORE_QUEUE_NAME, json)

    def __send_message(self, uid, data_string, timestamp=None):

        if timestamp:
            timestamp = self.auto_timestamp(timestamp)
        else:
            timestamp = int(time.time())

        if not uid:
            uid = self.device_uid

        if not uid:
            raise Exception("Can not send data without valid Device UID!")

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

