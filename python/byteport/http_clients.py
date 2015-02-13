from . import socks
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import logging
from urllib.error import HTTPError
from .socksipyhandler import SocksiPyHandler

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
                 proxy_password=None,
                 initial_heartbeat=True
        ):

        self.namespace_name = namespace_name
        self.device_uid = default_device_uid
        self.api_key = api_key
        self.base_url = byteport_api_store_url+'%s' % namespace_name
        logging.info('Storing data to Byteport using %s/%s/' % (self.base_url, default_device_uid))

        # Ie. for tunneling HTTP via SSH, first do:
        # ssh -D 5000 -N username@sshserver.org
        if proxy_port is not None:
            #socks.setdefaultproxy(proxy_type, proxy_addr,
            #                      proxy_port, username=proxy_username, password=proxy_password)
            #socket.socket = socks.socksocket
            #socks.wrapmodule(urllib2)

            self.opener = urllib.request.build_opener(SocksiPyHandler(proxy_type, proxy_addr, proxy_port))
            logging.info("Connecting through type %s proxy at %s:%s" % (proxy_type, proxy_addr, proxy_port))
        else:
            self.opener = None

        # Make empty test call to verify the credentials
        if initial_heartbeat:
            # This can also act as heart beat, no need to send data to signal "online" in Byteport
            self.store()

    # Can use another device_uid to override the one used in the constructor
    # Useful for Clients that acts as proxies for other devices, ie. over a sensor-network
    def store(self, data=None, device_uid=None):
        if data is None:
            data = dict()
        if device_uid is None:
            device_uid = self.device_uid

        data['_key'] = self.api_key
        encoded_data = urllib.parse.urlencode(data)
        url = '%s/%s/?%s' % (self.base_url, device_uid, encoded_data)

        try:
            logging.debug(url)
            # Set a valid User agent tag since api.byteport.se is CloudFlared
            # TODO: add a proper user-agent and make sure CloudFlare can handle it
            if self.opener:
                response = self.opener.open(url)
            else:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                response = urllib.request.urlopen(req)
            logging.debug('Response: %s' % response.read())
        except urllib.error.URLError as e:
            logging.error('%s' % e)
            logging.info('Got URLError, make sure you have the correct network connections (ie. to the internet)!')
            if self.opener is not None:
                logging.info('Make sure your proxy settings are correct and you can connect to the proxy host you specified.')
            raise ByteportConnectException('Failed to connect to byteport, check your network and proxy settings and setup.')

        except HTTPError as http_error:
            logging.error('%s' % http_error)
            if http_error.code == 403:
                message = 'Verify that the namespace %s does allow writes by HTTP GET calls, and that the ' \
                          'API key is correct.' % self.namespace_name
                logging.info(message)
                raise ByteportAPIForbiddenException(message)
            if http_error.code == 404:
                message = 'Make sure the device %s is registered under ' \
                          'namespace %s.' % (device_uid, self.namespace_name)
                logging.info(message)
                raise ByteportAPINotFoundException(message)

    # Simple wrapper for logging with ease
    def log(self, message, level='info', device_uid=None):
        self.store({level: message}, device_uid)
