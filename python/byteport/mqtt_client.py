
from client_base import *

try:
    import paho.mqtt.client as mqtt
    from paho.mqtt.client import error_string

except ImportError:
    print "Could not import MQTT library. The MQTT client will not be supported."
    print ""
    print "If you need to use that client, please do:"
    print "pip install paho-mqtt"

class ByteportMQTTClient(AbstractByteportClient):
    DEFAULT_BROKER_HOSTS = ['broker.igw.se', 'broker1.igw.se', 'broker2.igw.se', 'broker3.igw.se']
    QUEUE_NAME = '/queue/simple_string_dev_message'

    def __init__(self, namespace, device_uid, username, password, broker_hosts=DEFAULT_BROKER_HOSTS):

        self.namespace = str(namespace)

        guid = '%s.%s' % (namespace, device_uid)

        for broker_host in broker_hosts:

            self.client = mqtt.Client(client_id=guid, clean_session=False)
            self.client.username_pw_set(username, password)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message

            print "Connecting to %s" % broker_host

            self.client.connect(broker_host, 1883, 60)

            # Blocking call that processes network traffic, dispatches callbacks and
            # handles reconnecting.
            # Other loop*() functions are available that give a threaded interface and a
            # manual interface.
            self.client.loop_forever()

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        print(error_string(rc))

        if rc != 0:
            raise ByteportConnectException("Error while connecting to MQTT Broker: " + error_string(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        # self.client.subscribe("/queue/mqtt_test")

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        print(msg.topic+" "+str(msg.payload))
