import urllib
import urllib2
import logging
from urllib2 import HTTPError


class ByteportHttpGetClient:
    BYTEPORT_API_URL = 'http://api.byteport.se/services/store/'

    def __init__(self, namespace_name, api_key, device_uid):
        self.namespace_name = namespace_name
        self.device_uid = device_uid
        self.api_key = api_key
        self.base_url = self.BYTEPORT_API_URL+u'%s/%s/' % (namespace_name, device_uid)
        logging.info("Storing data to Byteport using %s" % self.base_url)

    def store(self, data):
        data['_key'] = self.api_key
        encoded_data = urllib.urlencode(data)
        url = u'%s?%s' % (self.base_url, encoded_data)

        try:
            logging.debug(url)
            # Set a valid User agent tag since api.byteport.se is CloudFlared
            req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib2.urlopen(req)
            logging.debug(response.read())
        except HTTPError as http_error:
            logging.error(u'%s' % http_error)
            if http_error.code == 403:
                logging.info(
                    "Verify that the namespace %s does allow writes by HTTP GET calls, and that the API key is correct."
                    % self.namespace_name)
            if http_error.code == 404:
                logging.info(
                    "Make sure the device %s is registered under namespace %s."
                    % (self.device_uid, self.namespace_name))
