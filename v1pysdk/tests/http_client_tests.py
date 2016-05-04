from v1pysdk.client import HttpClient
from mock import *
import unittest

class TestHttpClient(unittest.TestCase):
    base_url = 'https://localhost/VersionOne/'
    username = 'usr'
    password = 'pass'

    @patch('v1pysdk.client.urllib2.HTTPPasswordMgrWithDefaultRealm')
    @patch('v1pysdk.client.urllib2.build_opener')
    def setUp(self, build_opener, HTTPPasswordMgr):
        self.manager = Mock()
        self.opener = Mock()
        build_opener.return_value = self.opener
        HTTPPasswordMgr.return_value = self.manager
        self.http_client = HttpClient(self.base_url, self.username, self.password)

    def test_constructor(self):
        self.assertEqual(1, self.opener.add_handler.call_count)
        self.assertEqual(1, self.manager.add_password.call_count)

    @patch('v1pysdk.client.Request')
    def test_get(self, request):
        r = Mock()
        request.return_value = r

        self.http_client.get('http://get.com')

        request.assert_called_with('http://get.com')
        r.add_header.assert_called_with('Content-Type', 'text/xml;charset=UTF-8')
        self.opener.open.assert_called_with(r)

    @patch('v1pysdk.client.Request')
    def test_post(self, request):
        r = Mock()
        request.return_value = r
        data = Mock()

        self.http_client.post('http://post.com', data)

        request.assert_called_with('http://post.com', data)
        r.add_header.assert_called_with('Content-Type', 'text/xml;charset=UTF-8')
        self.opener.open.assert_called_with(r)

    if __name__ == '__main__':
        unittest.main()
