# -*- coding: utf-8 -*-
import unittest

from http_clients import *

'''

NOTE: All tests here need a Byteport instance to communicate with

'''
class TestHttpClients(unittest.TestCase):

    byteport_api_hostname = 'api.byteport.se'
    #byteport_api_hostname = 'acc.byteport.se'
    #byteport_api_hostname = 'localhost:8000'

    key = 'd8a26587463268f88fea6aec'
    #key = 'd74f48f8375a32ca632fa49a'
    #key = 'TEST'

    namespace = 'test'
    device_uid = 'byteport-api-tests'

    test_user = 't3stusr'
    test_password = 't3stusr'

    def test_should_store_string_to_single_field_name_using_GET_client(self):
        client = ByteportHttpClient(
            byteport_api_hostname=self.byteport_api_hostname,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid
        )

        data = {'string': 'hello string'}

        # Will raise exception upon errors
        client.store(data)

    def test_should_store_data_series_using_GET_client(self):
        client = ByteportHttpGetClient(
            byteport_api_hostname=self.byteport_api_hostname,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid
        )

        for v in range(0, 10):
            data = {'ramp': float(v)+0.0001}
            client.store(data)
            time.sleep(0.2)

    def test_should_store_utf8_convertibel_string_to_single_field_name_using_GET_client(self):
        client = ByteportHttpGetClient(
            byteport_api_hostname=self.byteport_api_hostname,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid
        )

        # Unicode string that can be converted to UTF-8
        data = {'unicode_string': u'mötley crüe'}

        client.store(data)

    def test_should_not_store_non_utf8_convertible_string_to_single_field_name_using_GET_client(self):
        client = ByteportHttpGetClient(
            byteport_api_hostname=self.byteport_api_hostname,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid
        )

        # A sting that can not be encoded to UTF-8: exception should be thrown client side
        data = {'unicode_string': '\x80'}

        self.assertRaises(ByteportClientInvalidDataTypeException, client.store, data)

    def test_should_store_number_to_single_field_name_using_GET_client(self):
        client = ByteportHttpGetClient(
            byteport_api_hostname=self.byteport_api_hostname,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid
        )

        data = {'number': 1337}

        # Will raise exception upon errors
        client.store(data)

    def test_should_store_number_to_single_field_name_with_custom_high_prec_timestamp_using_GET_client(self):
        client = ByteportHttpGetClient(
            byteport_api_hostname=self.byteport_api_hostname,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid
        )

        data = {'number': 1338}

        # Will raise exception upon errors
        custom_timestamp = datetime.datetime.strptime('2015-05-01T00:00:00.012345', '%Y-%m-%dT%H:%M:%S.%f')
        client.store(data, timestamp=custom_timestamp)

    def test_should_log_info_using_GET_client(self):
        client = ByteportHttpGetClient(
            byteport_api_hostname=self.byteport_api_hostname,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid
        )

        # Will raise exception upon errors
        client.log('info from integration tests using GET API. Lets repete this boring message just to get a shit load of text so it wont be truncated anywhere along the way: info from integration tests using GET APIinfo from integration tests using GET APIinfo from integration tests using GET APIinfo from integration tests using GET APIinfo from integration tests using GET APIinfo from integration tests using GET APIinfo from integration tests using GET API', 'info')

    def test_should_log_info_using_POST_client(self):
        client = ByteportHttpClient(
            byteport_api_hostname=self.byteport_api_hostname,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid
        )

        # Will raise exception upon errors
        client.log('info from integration tests using POST API', 'info')

    def test_should_store_string_to_single_field_name_using_POST_client(self):
        client = ByteportHttpClient(
            byteport_api_hostname=self.byteport_api_hostname,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid
        )

        data = {'fukt': 20}

        # Will raise exception upon errors
        client.store(data)

    def test_should_store_text_data_base64_encoded_to_single_field_name_using_POST_client(self):
        client = ByteportHttpClient(
            byteport_api_hostname=self.byteport_api_hostname,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid
        )

        field_name = 'string_b64'

        data_block = 'hello world'

        # Will raise exception upon errors
        client.base64_encode_and_store(field_name, data_block)

    def test_should_store_binary_data_to_single_field_name_using_POST_client(self):
        client = ByteportHttpClient(
            byteport_api_hostname=self.byteport_api_hostname,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid
        )

        field_name = 'bin_b64'

        binary_data = '\x10\x20\x30\x40'

        # Will raise exception upon errors
        client.base64_encode_and_store(field_name, binary_data)

    def test_should_compress_and_store_binary_data_to_single_field_name_using_POST_client(self):
        client = ByteportHttpClient(
            byteport_api_hostname=self.byteport_api_hostname,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid
        )

        field_name = 'bin_gzip_b64'

        binary_data = '\x10\x20\x30\x40'

        # Will raise exception upon errors
        client.base64_encode_and_store(field_name, binary_data, compression='gzip')

    def test_should_store_10K_binary_data_to_single_field_name_using_POST_client(self):
        client = ByteportHttpClient(
            byteport_api_hostname=self.byteport_api_hostname,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid
        )

        field_name = 'large_bin_b64'

        binary_data_base = '\x00\x10\x20\x30\x40\x50\x60\x70\x80\x90'
        data_buffer = bytearray()

        # Make a 10K buffer
        for i in range(0, 1000):
            data_buffer.extend(binary_data_base)

        # Will raise exception upon errors
        client.base64_encode_and_store(field_name, bytes(data_buffer))

    def test_should_store_10K_binary_data_and_gzip_to_single_field_name_using_POST_client(self):
        client = ByteportHttpClient(
            byteport_api_hostname=self.byteport_api_hostname,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid
        )

        field_name = 'large_bin_gzip_b64'

        binary_data_base = '\x00\x10\x20\x30\x40\x50\x60\x70\x80\x90'
        data_buffer = bytearray()

        # Make a 10K buffer
        for i in range(0, 1000):
            data_buffer.extend(binary_data_base)

        # Will raise exception upon errors
        client.base64_encode_and_store(field_name, bytes(data_buffer), compression='gzip')

    def test_should_store_10K_binary_data_and_bzip2_to_single_field_name_using_POST_client(self):
        client = ByteportHttpClient(
            byteport_api_hostname=self.byteport_api_hostname,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid
        )

        field_name = 'large_bin_bzip2_b64'

        binary_data_base = '\x00\x10\x20\x30\x40\x50\x60\x70\x80\x90'
        data_buffer = bytearray()

        # Make a 10K buffer
        for i in range(0, 1000):
            data_buffer.extend(binary_data_base)

        # Will raise exception upon errors
        client.base64_encode_and_store(field_name, bytes(data_buffer), compression='bzip2')

    def test_should_store_test_file_single_field_name_using_POST_client(self):
        client = ByteportHttpClient(
            byteport_api_hostname=self.byteport_api_hostname,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid
        )

        field_name = 'file_integer_raw'

        # Will raise exception upon errors
        client.store_file(field_name, './integer.txt')

    def test_should_store_test_file_and_bzip2_to_single_field_name_using_POST_client(self):
        client = ByteportHttpClient(
            byteport_api_hostname=self.byteport_api_hostname,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid
        )

        field_name = 'file_bzip2_b64'

        # Will raise exception upon errors
        client.base64_encode_and_store_file(field_name, './test_file_for_integration_tests.txt', compression='bzip2')

    def test_should_store_directory(self):
        client = ByteportHttpClient(
            byteport_api_hostname=self.byteport_api_hostname,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid,
            initial_heartbeat=False
        )
        client.store_directory('./test_directory', 'dir_storing_test')

    def test_should_login_with_correct_credentials(self):
        client = ByteportHttpClient(
            byteport_api_hostname=self.byteport_api_hostname
        )

        client.login(self.test_user, self.test_password)

    def test_should_not_login_with_invalid_credentials(self):
        client = ByteportHttpClient(
            byteport_api_hostname=self.byteport_api_hostname,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid,
            initial_heartbeat=False
        )

        try:
            client.login('user', 'f00passb4r')
        except ByteportLoginFailedException:
            return

        raise Exception("ByteportLoginFailedException was NOT thrown during invalid login!")

    def test_should_login_and_access_protected_resource(self):
        client = ByteportHttpClient(
            byteport_api_hostname=self.byteport_api_hostname
        )

        client.login(self.test_user, self.test_password)

        # List Namespaces
        result = client.list_namespaces()
        self.assertTrue(len(result) > 0)

        # Query for matching devices
        result = client.query_devices('test', full=False, limit=10)
        self.assertTrue(len(result) > 0)

        # Load one device
        result = client.get_device('test', '6000')
        self.assertEqual(result[0]['guid'], 'test.6000')

        # List devices in one namespace, load both as list and full
        result = client.list_devices('test', full=False)
        for guid in result:
            self.assertTrue(len(guid) > 0)

        result = client.list_devices('test', full=True)

        for device in result:
            self.assertTrue(len(device['device_type']) > 0)

        # Load time-series data
        to_time = datetime.datetime.now()
        from_time = to_time - datetime.timedelta(hours=1)
        result = client.load_timeseries_data('test', '6000', 'temp', from_time, to_time)
        self.assertEqual(result['meta']['path'], u'test.6000.temp')


class PollingTests(unittest.TestCase):

    #hostname = 'localhost:8000'
    #hostname = 'acc.byteport.se'
    hostname = 'api.byteport.se'
    byteport_api_hostname = 'http://%s/services/store/' % hostname

    namespace = 'test'
    device_uid = 'byteport-api-tests'
    key = 'd8a26587463268f88fea6aec'
    #key = 'TEST'

    def test_should_poll_directory_for_changes___needs_manual_change_to_trigger(self):
        client = ByteportHttpClient(
            byteport_api_hostname=self.byteport_api_hostname,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid,
            initial_heartbeat=False
        )
        client.poll_directory_and_store_upon_content_change('./test_directory/', 'dir_poller_test')


class TestStompClient(unittest.TestCase):

    TEST_BROKERS = ['canopus']

    test_device_uid = '6000'

    def test_should_connect_and_send_one_message_using_stomp_client(self):

        client = ByteportStompClient('test', 'publicTestUser', 'publicTestUser', broker_hosts=self.TEST_BROKERS)

        client.store({'stomp_data': 'hello STOMP world!'}, self.test_device_uid)
