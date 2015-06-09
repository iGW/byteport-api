import socks
import urllib
import urllib2
import logging
import base64
import zlib
import bz2

from urllib2 import HTTPError
from socksipyhandler import SocksiPyHandler

DEFAULT_BYTEPORT_API_STORE_URL = 'http://api.byteport.se/services/store/'
DEFAULT_BYTEPORT_API_STORE_URL_HTTPS = 'http://api.byteport.se/services/store/'

class ByteportAPIException(Exception):
    pass

class ByteportConnectException(ByteportAPIException):
    pass

class ByteportAPIForbiddenException(ByteportAPIException):
    pass

class ByteportAPINotFoundException(ByteportAPIException):
    pass

class ByteportClkentUnsupportedCompression(ByteportAPIException):
    pass

class ByteportHttpClientBase:

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
            self.opener = urllib2.build_opener(SocksiPyHandler(proxy_type, proxy_addr, proxy_port))
            logging.info("Connecting through type %s proxy at %s:%s" % (proxy_type, proxy_addr, proxy_port))
        else:
            self.opener = None

        # Make empty test call to verify the credentials
        if initial_heartbeat:
            # This can also act as heart beat, no need to send data to signal "online" in Byteport
            self.store()

    def store(self, data=None, device_uid=None):
        raise NotImplementedError("Store is not implemented in this class")

    def make_request(self, url, device_uid, data=None):

        try:
            logging.debug(url)
            # Set a valid User agent tag since api.byteport.se is CloudFlared
            # TODO: add a proper user-agent and make sure CloudFlare can handle it
            if self.opener:
                response = self.opener.open(url)
            else:
                # NOTE: If data != None, the request will be a POST request instead
                if data is not None:
                    data = urllib.urlencode(data)
                req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'}, data=data)

                response = urllib2.urlopen(req)
            logging.debug(u'Response: %s' % response.read())

        except HTTPError as http_error:
            logging.error(u'%s' % http_error)
            if http_error.code == 403:
                message = u'Verify that the namespace %s does allow writes by HTTP, and also if the correct' \
                          u'request method is set and usd (ie GET and/or POST), and that the ' \
                          u'API key is correct.' % self.namespace_name
                logging.info(message)
                raise ByteportAPIForbiddenException(message)
            if http_error.code == 404:
                message = u'Make sure the device %s is registered under ' \
                          u'namespace %s.' % (device_uid, self.namespace_name)
                logging.info(message)
                raise ByteportAPINotFoundException(message)

        except urllib2.URLError as e:
            logging.error(u'%s' % e)
            logging.info(u'Got URLError, make sure you have the correct network connections (ie. to the internet)!')
            if self.opener is not None:
                logging.info(u'Make sure your proxy settings are correct and you can connect to the proxy host you specified.')
            raise ByteportConnectException(u'Failed to connect to byteport, check your network and proxy settings and setup.')

    # Simple wrapper for logging with ease
    def log(self, message, level='info', device_uid=None):
        self.store({level: message}, device_uid)


class ByteportHttpPostClient(ByteportHttpClientBase):

    #
    #    Store a single file vs a field name to Byteport via HTTP POST with optional compresstion
    #
    def base64_encode_and_store_store_file(self, field_name, path_to_file, device_uid=None, compression=None):
        with open(path_to_file, 'r') as content_file:
            file_data = content_file.read()
            self.base64_encode_and_store_store(field_name, file_data, device_uid, compression)

    #
    #    Store a single data block vs a field name to Byteport via HTTP POST
    #
    def base64_encode_and_store_store(self, field_name, fileobj, device_uid=None, compression=None):
        if compression is None:
            data_block = fileobj
        elif compression == 'gzip':
            data_block = zlib.compress(fileobj)
        elif compression == 'bzip2':
            data_block = bz2.compress(fileobj)
        else:
            raise ByteportClkentUnsupportedCompression("Unsupported compression method '%s'" % compression)

        data = {field_name: base64.b64encode(data_block)}

        self.store(data, device_uid)

    def store(self, data=None, device_uid=None):
        if data is None:
            data = dict()
        if device_uid is None:
            device_uid = self.device_uid

        data['_key'] = self.api_key
        url = '%s/%s/' % (self.base_url, device_uid)

        self.make_request(url, device_uid, data)


class ByteportHttpGetClient(ByteportHttpClientBase):

    # Can use another device_uid to override the one used in the constructor
    # Useful for Clients that acts as proxies for other devices, ie. over a sensor-network
    def store(self, data=None, device_uid=None):
        if data is None:
            data = dict()
        if device_uid is None:
            device_uid = self.device_uid

        data['_key'] = self.api_key
        encoded_data = urllib.urlencode(data)
        url = '%s/%s/?%s' % (self.base_url, device_uid, encoded_data)

        self.make_request(url, device_uid)
