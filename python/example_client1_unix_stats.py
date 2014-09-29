import os
import time
import sys
import socket
import logging
import re
from byteport.http_clients import ByteportHttpGetClient


def collect_load_data(byteport_client, interval_sec=60):

    while True:
        loadavg = os.getloadavg()

        unix_stats = dict()
        unix_stats['la1'] = loadavg[0]
        unix_stats['la5'] = loadavg[1]
        unix_stats['la15'] = loadavg[2]

        try:
            byteport_client.store(unix_stats)
        except Exception as e:
            # Catch and logg all errors and try again later is OK in this kind of use case
            logging.error(u'Error during Byteport API call: %s' % e)
        time.sleep(interval_sec)

'''
Simple script that collects three load figures from the system and uses the Byteport client
API class to post them to api.byteport.se.
'''
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.debug('====>>> Note DEBUG log level is enabled by default in this example client.')

    if len(sys.argv) < 3:
        print "Usage: %s <namespace name> <namespace api write key> [device uid]" % sys.argv[0]
        exit(1)

    namespace = sys.argv[1]
    namespace_api_write_key = sys.argv[2]

    try:
        device_uid = sys.argv[3]
    except Exception:
        hostname = socket.gethostname()
        device_uid = re.sub('[^0-9a-zA-Z]+', '_', hostname)

    client = ByteportHttpGetClient(namespace, namespace_api_write_key, device_uid)
    collect_load_data(client, 30)
