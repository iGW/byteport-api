import socks
import socket
import urllib
import urllib2
import logging
from urllib2 import HTTPError

DEFAULT_BYTEPORT_API_STORE_URL = 'http://api.byteport.se/services/store/'

class ByteportAPIException(Exception):
    pass

class ByteportConnectException(ByteportAPIException):
    pass

class ByteportAPIForbiddenException(ByteportAPIException):
    pass

class ByteportAPINotFoundException(ByteportAPIException):
    pass

class ByteportHttpGetClient:

    def __init__(self,
                 namespace_name,
                 api_key,
                 default_device_uid,
                 byteport_api_store_url=DEFAULT_BYTEPORT_API_STORE_URL,
                 proxy_type=socks.PROXY_TYPE_SOCKS5,
                 proxy_addr="127.0.0.1",
                 proxy_port=None,
                 proxy_username=None,
                 proxy_password=None
        ):

        self.namespace_name = namespace_name
        self.device_uid = default_device_uid
        self.api_key = api_key
        self.base_url = byteport_api_store_url+'%s' % namespace_name
        logging.info('Storing data to Byteport using %s/%s/' % (self.base_url, default_device_uid))

        # Ie. for tunneling HTTP via SSH, first do:
        # ssh -D 5000 -N username@sshserver.org
        if proxy_port is not None:
            socks.setdefaultproxy(proxy_type, proxy_addr,
                                  proxy_port, username=proxy_username, password=proxy_password)
            socket.socket = socks.socksocket
            socks.wrapmodule(urllib2)
            self.using_proxy = True
        else:
            self.using_proxy = False

        # Make empty test call to verify the credentials
        self.store()

    # Can use another device_uid to override the one used in the constructor
    # Useful for Clients that acts as proxies for other devices, ie. over a sensor-network
    def store(self, data=None, device_uid=None):
        if data is None:
            data = dict()
        if device_uid is None:
            device_uid = self.device_uid

        data['_key'] = self.api_key
        encoded_data = urllib.urlencode(data)
        url = u'%s/%s/?%s' % (self.base_url, device_uid, encoded_data)

        try:
            logging.debug(url)
            # Set a valid User agent tag since api.byteport.se is CloudFlared
            # TODO: add a proper user-agent and make sure CloudFlare can handle it
            req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib2.urlopen(req)
            logging.debug(u'Response: %s' % response.read())
        except urllib2.URLError as e:
            logging.error(u'%s' % e)
            logging.info(u'Got URLError, make sure you have the correct network connections (ie. to the internet)!')
            if self.using_proxy:
                logging.info(u'Make sure your proxy settings are correct and you can connect to the proxy host you specified.')
            raise ByteportConnectException(u'Failed to connect to byteport, check your network and proxy settings and setup.')

        except HTTPError as http_error:
            logging.error(u'%s' % http_error)
            if http_error.code == 403:
                message = u'Verify that the namespace %s does allow writes by HTTP GET calls, and that the ' \
                          u'API key is correct.' % self.namespace_name
                logging.info(message)
                raise ByteportAPIForbiddenException(message)
            if http_error.code == 404:
                message = u'Make sure the device %s is registered under ' \
                          u'namespace %s.' % (device_uid, self.namespace_name)
                logging.info(message)
                raise ByteportAPINotFoundException(message)