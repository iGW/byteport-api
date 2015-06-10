import unittest
import datetime

from http_clients import ByteportHttpGetClient, ByteportHttpPostClient

'''

NOTE: All tests here need a Byteport instance to communicate with

'''
class TestHttpClients(unittest.TestCase):

    hostname = 'localhost:8000'
    # hostname = 'api.byteport.se'
    byteport_api_store_url = 'http://%s/services/store/' % hostname

    namespace = 'test'
    device_uid = '6000'
    key = 'TEST'

    def test_should_store_string_to_single_field_name_using_GET_client(self):
        client = ByteportHttpGetClient(
            byteport_api_store_url=self.byteport_api_store_url,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid
        )

        data = {'string': 'hello string'}

        # Will raise exception upon errors
        client.store(data)

    def test_should_store_number_to_single_field_name_using_GET_client(self):
        client = ByteportHttpGetClient(
            byteport_api_store_url=self.byteport_api_store_url,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid
        )

        data = {'number': 1337}

        # Will raise exception upon errors
        client.store(data)

    def test_should_store_number_to_single_field_name_with_custom_high_prec_timestamp_using_GET_client(self):
        client = ByteportHttpGetClient(
            byteport_api_store_url=self.byteport_api_store_url,
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
            byteport_api_store_url=self.byteport_api_store_url,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid
        )

        # Will raise exception upon errors
        client.log('info from integration tests using GET API', 'info')

    def test_should_log_info_using_POST_client(self):
        client = ByteportHttpPostClient(
            byteport_api_store_url=self.byteport_api_store_url,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid
        )

        # Will raise exception upon errors
        client.log('info from integration tests using POST API', 'info')

    def test_should_store_string_to_single_field_name_using_POST_client(self):
        client = ByteportHttpPostClient(
            byteport_api_store_url=self.byteport_api_store_url,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid
        )

        data = {'fukt': 20}

        # Will raise exception upon errors
        client.store(data)

    def test_should_store_text_data_base64_encoded_to_single_field_name_using_POST_client(self):
        client = ByteportHttpPostClient(
            byteport_api_store_url=self.byteport_api_store_url,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid
        )

        field_name = 'string_b64'

        data_block = 'hello world'

        # Will raise exception upon errors
        client.base64_encode_and_store_store(field_name, data_block)

    def test_should_store_binary_data_to_single_field_name_using_POST_client(self):
        client = ByteportHttpPostClient(
            byteport_api_store_url=self.byteport_api_store_url,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid
        )

        field_name = 'bin_b64'

        binary_data = '\x10\x20\x30\x40'

        # Will raise exception upon errors
        client.base64_encode_and_store_store(field_name, binary_data)

    def test_should_compress_and_store_binary_data_to_single_field_name_using_POST_client(self):
        client = ByteportHttpPostClient(
            byteport_api_store_url=self.byteport_api_store_url,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid
        )

        field_name = 'bin_gzip_b64'

        binary_data = '\x10\x20\x30\x40'

        # Will raise exception upon errors
        client.base64_encode_and_store_store(field_name, binary_data, compression='gzip')

    def test_should_store_10K_binary_data_to_single_field_name_using_POST_client(self):
        client = ByteportHttpPostClient(
            byteport_api_store_url=self.byteport_api_store_url,
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
        client.base64_encode_and_store_store(field_name, bytes(data_buffer))

    def test_should_store_10K_binary_data_and_gzip_to_single_field_name_using_POST_client(self):
        client = ByteportHttpPostClient(
            byteport_api_store_url=self.byteport_api_store_url,
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
        client.base64_encode_and_store_store(field_name, bytes(data_buffer), compression='gzip')

    def test_should_store_10K_binary_data_and_bzip2_to_single_field_name_using_POST_client(self):
        client = ByteportHttpPostClient(
            byteport_api_store_url=self.byteport_api_store_url,
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
        client.base64_encode_and_store_store(field_name, bytes(data_buffer), compression='bzip2')

    def test_should_store_test_file_and_bzip2_to_single_field_name_using_POST_client(self):
        client = ByteportHttpPostClient(
            byteport_api_store_url=self.byteport_api_store_url,
            namespace_name=self.namespace,
            api_key=self.key,
            default_device_uid=self.device_uid
        )

        field_name = 'file_bzip2_b64'

        # Will raise exception upon errors
        client.base64_encode_and_store_store_file(field_name, './test_file_for_integration_tests.txt', compression='bzip2')
