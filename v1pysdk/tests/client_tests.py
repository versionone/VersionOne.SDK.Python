from v1pysdk.client import V1Server, HttpClient
from mock import *
import unittest


class TestV1Server(unittest.TestCase):
    address = 'local'
    instance = 'V1'
    username = 'usr'
    password = 'pass'
    scheme = 'https'

    @patch('v1pysdk.client.HttpClient')
    def setUp(self, http_client):
        self.http_client = http_client
        http_client.return_value = self.client = Mock()
        self.client.get.return_value = (None, '<root><get>response</get></root>')
        self.client.post.return_value = (None, '<root><post>response</post></root>')

        self.server = V1Server(self.address, self.instance, self.username, self.password, self.scheme)

    def test_constructor(self):
        self.assertEqual(1, self.http_client.call_count)

    def test_build_url(self):
        # {'sel': 'Name', 'Where': "AssetState='64','Name='No importa'"}
        url = self.server.build_url('mypath', {'a': 'b'}, 'myfragment')
        self.assertEqual('https://local/V1/mypath?a=b#myfragment', url)

    def test_get_asset_xml(self):
        xml = self.server.get_asset_xml('Story', '123')

        self.client.get.assert_called_once_with('https://local/V1/rest-1.v1/Data/Story/123')
        self.assertEqual('root', xml.tag)

    def test_get_query_xml(self):
        xml = self.server.get_query_xml('Data', 'Story', "Name='My Story';AssetState='64'", 'Name,Number')

        self.client.get \
            .assert_called_once_with(
            'https://local/V1/rest-1.v1/Data/Story?sel=Name%2CNumber&Where=Name%3D%27My+Story%27%3BAssetState%3D%2764%27')
        self.assertEqual('root', xml.tag)

    def test_get_meta_xml(self):
        xml = self.server.get_meta_xml('Story')

        self.client.get \
            .assert_called_once_with('https://local/V1/meta.v1/Story')
        self.assertEqual('root', xml.tag)

    def test_execute_operation(self):
        xml = self.server.execute_operation('Story', '1234', 'Inactivate')

        self.client.post.assert_called_once_with('https://local/V1/rest-1.v1/Data/Story/1234?op=Inactivate',
                                                 postdata={})
        self.assertEqual('root', xml.tag)

    def test_get_attr_without_moment(self):
        xml = self.server.get_attr(asset_type_name='Story', oid='1234', attrname='AssetState')

        self.client.get.assert_called_once_with('https://local/V1/rest-1.v1/Data/Story/1234/AssetState')
        self.assertEqual('root', xml.tag)

    def test_get_attr_with_moment(self):
        xml = self.server.get_attr(asset_type_name='Story', oid='1234', attrname='AssetState', moment='1016')

        self.client.get.assert_called_once_with('https://local/V1/rest-1.v1/Data/Story/1234/1016/AssetState')
        self.assertEqual('root', xml.tag)

        if __name__ == '__main__':
            unittest.main()


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
