from v1pysdk.client import V1Server
from mock import *
import unittest

class TestClient(unittest.TestCase):
    address = 'local'
    instance = 'V1'
    username = 'usr'
    password = 'pass'
    scheme = 'https'

    @patch('v1pysdk.client.urllib2.HTTPPasswordMgrWithDefaultRealm')
    @patch('v1pysdk.client.urllib2.build_opener')
    def setUp(self, build_opener, HTTPPasswordMgr):
        self.manager = Mock()
        self.opener = Mock()

        build_opener.return_value = self.opener
        HTTPPasswordMgr.return_value = self.manager

        self.server = V1Server(self.address, self.instance, self.username, self.password, self.scheme)

    def tearDown(self):
        print 'nothing to do here'

    def test_constructor(self):
        assert self.opener.add_handler.call_count is 1
        assert self.manager.add_password.call_count is 1

    @patch('v1pysdk.client.Request')
    def test_http_get(self, request):
        r = Mock()
        request.return_value = r

        self.server.http_get('http://get.com')

        request.assert_called_with('http://get.com')
        r.add_header.assert_called_with('Content-Type', 'text/xml;charset=UTF-8')
        self.opener.open.assert_called_with(r)

    @patch('v1pysdk.client.Request')
    def test_http_post(self, request):
        r = Mock()
        request.return_value = r
        data = Mock()

        self.server.http_post('http://post.com', data)

        request.assert_called_with('http://post.com', data)
        r.add_header.assert_called_with('Content-Type', 'text/xml;charset=UTF-8')
        self.opener.open.assert_called_with(r)

    def test_build_url(self):
        url = self.server.build_url('mypath', {'a': 'b'}, 'myfragment')
        self.assertEqual('https://local/V1/mypath?a=b#myfragment', url)

    if __name__ == '__main__':
        unittest.main()


