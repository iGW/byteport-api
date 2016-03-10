import datetime
import re

# Non standard imports, try to reduce if possible
import pytz

class ByteportClientException(Exception):
    pass


class ByteportConnectException(ByteportClientException):
    pass

class ByteportLoginFailedException(Exception):
    pass


class ByteportClientForbiddenException(ByteportClientException):
    pass


class ByteportClientDeviceNotFoundException(ByteportClientException):
    pass


class ByteportClientUnsupportedCompressionException(ByteportClientException):
    pass


class ByteportClientUnsupportedTimestampTypeException(ByteportClientException):
    pass


class ByteportClientInvalidFieldNameException(ByteportClientException):
    pass


class ByteportClientInvalidDataTypeException(ByteportClientException):
    pass

class ByteportServerException(ByteportClientException):
    pass


class AbstractByteportClient:

    # Byteport supports milli-second precision timestamps but this client sends micro-second precision
    # timestamps if possible to support a possible future enhancement.
    #
    # Helper that can take a timestamp as epoch as string or number, or a datetime object
    # it will return a unix epoch as float converted to a string since we do not want
    # the string conversion to be left to other layers leading to possible precision
    # or rounding errors
    def auto_timestamp(self, timestamp):
        if type(timestamp) is int:
            fs = float(timestamp)
        elif type(timestamp) is float:
            fs = timestamp
        elif type(timestamp) is datetime.datetime:
            as_utc = self.timestamp_as_utc(timestamp)
            as_micros = self.unix_time_micros(as_utc)
            fs = as_micros / 1e6
        else:
            raise ByteportClientUnsupportedTimestampTypeException("Invalid format for auto_timestamp(): " % type(timestamp))

        # Will not leave trailing zeros, see
        # http://stackoverflow.com/questions/2440692/formatting-floats-in-python-without-superfluous-zeros
        return ('%f' % fs).rstrip('0').rstrip('.')

    def unix_time_micros(self, datetime_object):
        td = (datetime_object - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc))
        u_secs = td.microseconds + ((td.seconds + td.days * 24 * 3600) * 10**6)
        return u_secs

    def timestamp_as_utc(self, datetime_object):
        if datetime_object.tzinfo:
            return datetime_object
        else:
            return pytz.utc.localize(datetime_object)

    def special_match(self, strg, search=re.compile(r'[^-a-zA-Z0-9_:]').search):
        return not bool(search(strg))

    def verify_name(self, name):
        if len(name) < 1 or len(name) > 32:
            return False

        if name.startswith('-') or name.startswith('_') or name.endswith('-') or name.endswith('_'):
            return False

        return self.special_match(name)

    def verify_field_name(self, field_name):
        try:
            self.verify_name(field_name)
        except Exception:
            raise ByteportClientInvalidFieldNameException()

    def utf8_encode_value(self, value):
        try:
            # Any string that can be UTF-8 encoded are valid data for Byteport HTTP API
            return (u'%s' % value).encode('utf8')
        except Exception:
            raise ByteportClientInvalidDataTypeException()

    def convert_data_to_utf8(self, data):
        utf8_data = dict()
        for field_name, value in data.iteritems():
            self.verify_field_name(field_name)
            value_as_utf8 = self.utf8_encode_value(value)

            utf8_data[field_name] = value_as_utf8

        return utf8_data
