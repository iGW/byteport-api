import unittest
import threading
import time

from clients import ByteportHttpClient

class PollingTests(unittest.TestCase):

    def setUp(self):

        self.client = ByteportHttpClient('test', 'd8a26587463268f88fea6aec', 'barDev1', initial_heartbeat=False)

        self.pt = PollingThread()

        self.pt.set_client(self.client)

    def test_should_detect_change_in_a_directory(self):
        #
        # Force a chagne in the directory
        #

        # TODO: Finish building this test
        return

        self.pt.run()

        time.sleep(1)

        self.pt.join()





class PollingThread(threading.Thread):

    def set_client(self, client):
        self.client = client

    def run(self):

        # NOTE: This will block the current thread!
        self.client.poll_directory_and_store_upon_content_change('./test_directory/', 'barDev1', poll_interval=10)
