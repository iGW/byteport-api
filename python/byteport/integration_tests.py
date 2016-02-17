# -*- coding: utf-8 -*-
import unittest

from http_clients import *
from stomp_client import *
from mqtt_client import *

'''

NOTE: All tests here need a Byteport instance to communicate with

'''
class TestHttpClients(unittest.TestCase):

    PRODUCTION = ('api.byteport.se', '(- LOOK IT UP -)', 'N/A', 'N/A')
    ACCEPTANCE = ('acc.byteport.se', 'd74f48f8375a32ca632fa49a', 'N/A', 'N/A')
    LOCALHOST = ('localhost:8000', 'TEST', 'admin', 'admin')

    TEST_ENVIRONMENT = LOCALHOST

    byteport_api_hostname = TEST_ENVIRONMENT[0]
    key = TEST_ENVIRONMENT[1]
    test_user = TEST_ENVIRONMENT[2]
    test_password = TEST_ENVIRONMENT[3]

    namespace = 'test'
    device_uid = 'byteport-api-tests'

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

    def test_should_receive_error_for_missing_deviceuid_using_GET_client(self):
        try:
            client = ByteportHttpClient(
                byteport_api_hostname=self.byteport_api_hostname,
                namespace_name=self.namespace,
                api_key=self.key,
                default_device_uid=''
            )

            data = {'string': 'hello string'}

            # Will raise exception upon errors
            client.store(data)
        except ByteportClientDeviceNotFoundException:
            return

        raise Exception("Unit under test did not raise the correct exception!")

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

    def test_should_login_and_logout_and_not_have_access_after(self):
        client = ByteportHttpClient(
            byteport_api_hostname=self.byteport_api_hostname
        )

        client.login(self.test_user, self.test_password)

        client.logout()

        try:
            client.list_namespaces()
        except Exception as e:
            return

        raise Exception("list_namespaces() did not raise exception after logout!")

    def test_should_not_login_with_invalid_credentials(self):
        client = ByteportHttpClient(
            byteport_api_hostname=self.byteport_api_hostname,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid,
            initial_heartbeat=False
        )

        try:
            client.login('fakeuser', 'f00passb4r')
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
        result = client.query_devices('test*', full=False, limit=10)
        self.assertTrue(len(result) > 1)

        # Load one device
        result = client.get_device('test', '6000')
        self.assertEqual(result[0]['guid'], 'test.6000')

        # Obtain a list of all UIDs in this namespace
        result = client.list_devices('test')

        for device in result:
            self.assertTrue(len(device['uid']) > 0)

        # Obtain a list of Devices (with contents)
        result = client.list_devices('test', 1)

        for device in result:
            self.assertTrue(len(device['active']) > 0)

        #Devices
        result = client.get_devices('test')
        self.assertTrue( len(result) > 0 )

        result = client.get_devices('test', "636744")
        self.assertTrue( len(result) == 0, "Should not find any device with id 636744, found: %s" % len(result) )

        result = client.get_devices('test', "TestGW")
        self.assertTrue( len(result) == 1, "Should only find one device with uid=TestGW., found %s" % len(result) )
        self.assertTrue( result[0][u'uid'] == u'TestGW', 'Device with id 1 should be the test GW, but was: "%s"' % result[0][u'uid'])


        #Devicetypes
        result = client.get_device_types('test')
        self.assertTrue( len(result) > 0 )

        result = client.get_device_types('test', "636744")
        self.assertTrue( len(result) == 0, "Should not find any devicetype with id 636744, found: %s" % len(result) )

        result = client.get_device_types('test', "1")
        self.assertTrue( len(result) == 1, "Should only find one devicetype with id=1, found %s" % len(result) )
        self.assertTrue( result[0][u'name'] == u'Generic Test Gateway', 'Device with id 1 should be the test GW, but was: "%s"' % result[0][u'name'])


        #device firmwares
        result = client.get_firmwares('test', device_type_id='1')
        self.assertTrue( len(result) > 0 )

        result = client.get_firmwares('test', device_type_id="1", key="636744")
        self.assertTrue( len(result) == 0, "Should not find any firmware with id 636744, found: %s" % len(result) )

        result = client.get_firmwares('test', device_type_id="1", key="2")
        self.assertTrue( len(result) == 1, "Should only find one device with id=1, found %s" % len(result) )
        self.assertTrue( result[0][u'filesize'] == u'6', 'Device fw with id 2 should have size 6, but was: "%s"' % result[0][u'filesize'])


        #device field-definitions
        result = client.get_field_definitions('test', device_type_id='2')
        self.assertTrue( len(result) > 0 )

        result = client.get_field_definitions('test', device_type_id="2", key="636744")
        self.assertTrue( len(result) == 0, "Should not find any field definition with id 636744, found: %s" % len(result) )

        result = client.get_field_definitions('test', device_type_id="2", key="5")
        self.assertTrue( len(result) == 1, "Should only find one field definition with id=1, found %s" % len(result) )
        self.assertTrue( result[0][u'name'] == u'b64_jsons', 'Device field 5 of test gw should be "b64_jsons", but was: "%s"' % result[0][u'name'])

    def test_should_login_and_access_timeseries_data(self):
        client = ByteportHttpClient(
            byteport_api_hostname=self.byteport_api_hostname
        )

        client.login(self.test_user, self.test_password)

        # List Namespaces
        result = client.list_namespaces()
        self.assertTrue(len(result) > 0)

        # Load time-series data
        to_time = datetime.datetime.now()
        from_time = to_time - datetime.timedelta(hours=1)
        result = client.load_timeseries_data_range('test', '6000', 'temp', from_time, to_time)
        self.assertEqual(result['meta']['path'], u'test.6000.temp')

        result = client.load_timeseries_data('test', '6000', 'temp', timedelta_minutes=180)
        self.assertEqual(result['meta']['path'], u'test.6000.temp')

    def test_should_login_and_send_message(self):
        client = ByteportHttpClient(
            byteport_api_hostname=self.byteport_api_hostname
        )

        client.login(self.test_user, self.test_password)

        message_to_device = 'hello from integration tests'
        response = client.send_message('test', '6000', message_to_device)

        # note the message SENT is also JSON, so there is another JSON structure embeedded in the response!
        message = json.loads(response['message'])

        self.assertEqual(message[0]['data'], message_to_device)

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

    TEST_BROKERS = ['acc.broker.byteport.se']

    test_device_uid = '6000'

    def test_should_connect_and_send_one_message_using_stomp_client(self):

        client = ByteportStompClient(
            'test', 'publicTestUser', 'publicTestUser', broker_hosts=self.TEST_BROKERS)

        client.store({'stomp_data': 'hello STOMP world!'}, self.test_device_uid)


class TestMQTTClient(unittest.TestCase):

    TEST_BROKERS = ['acc.broker.byteport.se']

    test_device_uid = '6000'

    def test_should_connect_using_mqtt_client(self):

        client = ByteportMQTTClient('test', self.test_device_uid, 'publicTestUser', 'publicTestUser', broker_hosts=self.TEST_BROKERS)
