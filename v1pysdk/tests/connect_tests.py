from testtools import TestCase
from testtools.matchers import Equals

from elementtree.ElementTree import fromstring

from v1pysdk.client import *

class TestV1Connection(TestCase):
  def test_connect(self, username='admin', password='admin'):
    client = HttpClient('http://www14.v1host.com/v1sdktesting', username=username, password=password)
    code, body = client.get('http://www14.v1host.com/v1sdktesting/rest-1.v1/Data/Story?sel=Name')
    print "\n\nCode: ", code
    print "Body: ", body
    elem = fromstring(body)
    self.assertThat(elem.tag, Equals('Assets'))