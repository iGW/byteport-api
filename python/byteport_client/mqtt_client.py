
from client_base import *
import json

try:
    import paho.mqtt.client as mqtt
    from paho.mqtt.client import error_string
    from paho.mqtt.client import MQTTv31, MQTTv311

except ImportError:
    print "Could not import MQTT library. The MQTT client will not be supported."
    print ""
    print "If you need to use that client, please do:"
    print "pip install paho-mqtt"

class ByteportMQTTClient(AbstractByteportClient):
    DEFAULT_BROKER_HOST = 'broker.byteport.se'
    PUBLISH_TOPIC = 'simple_string_dev_message'
    QOS_LEVEL = 0

    def __init__(self, namespace, device_uid, username, password,
                 broker_host=DEFAULT_BROKER_HOST, loop_forever=False, explicit_vhost=None):

        self.namespace = str(namespace)

        self.device_uid = device_uid

        self.guid = '%s.%s' % (namespace, device_uid)

        self.self_topic_name = self.guid

        if explicit_vhost:
            vhost = explicit_vhost
        else:
            vhost = namespace

        if vhost:
            username = '%s:%s' % (vhost, username)

        self.mqtt_client = mqtt.Client(client_id=self.guid, clean_session=False, protocol=MQTTv311)
        self.mqtt_client.username_pw_set(username, password)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        print "Connecting to %s" % broker_host

        rc = self.mqtt_client.connect(broker_host, 1883, 60)
        print('connect(): %s' % error_string(rc))

        # Blocking call that processes network traffic, dispatches callbacks and
        # handles reconnecting.
        # Other loop*() functions are available that give a threaded interface and a
        # manual interface.

        if loop_forever:
            self.mqtt_client.loop_forever()

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        print('on_connect: %s' % error_string(rc))

        if rc != 0:
            raise ByteportConnectException("Error while connecting to MQTT Broker: " + error_string(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        self.mqtt_client.subscribe(self.self_topic_name, qos=self.QOS_LEVEL)

        # For testing pub/subscribe via. RabbitMQ -> Exchange -> Queue
        self.mqtt_client.subscribe(self.PUBLISH_TOPIC, qos=self.QOS_LEVEL)

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        print(msg.topic+" "+str(msg.payload))

    def store(self, data_string):
        ssdm_packet = self.build_simple_string_device_message_packet(self.namespace, self.device_uid, data_string)

        json_string = json.dumps([ssdm_packet])

        self.store_raw(json_string)

    def store_raw(self, message):
        # TODO: Wrap in JSON packet

        # Publish with QoS=2
        # http://www.hivemq.com/blog/mqtt-essentials-part-6-mqtt-quality-of-service-levels
        (result, mid) = self.mqtt_client.publish(topic=self.PUBLISH_TOPIC, payload=message, qos=self.QOS_LEVEL)

        print "store(): %s" % error_string(result)

    def block(self):
        self.mqtt_client.loop_forever()

    def disconnect(self):
        self.mqtt_client.disconnect()
