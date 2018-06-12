from testtools import TestCase
from testtools.matchers import Equals

from elementtree.ElementTree import parse, fromstring, ElementTree

from .v1pysdk.client import *

class TestV1Connection(TestCase):
  def test_connect(self, username='admin', password='admin'):
    server = V1Server(address='www14.v1host.com', username=username, password=password,instance='v1sdktesting')
    code, body = server.fetch('/rest-1.v1/Data/Story?sel=Name')
    print("\n\nCode: ", code)
    print("Body: ", body)
    elem = fromstring(body)
    self.assertThat(elem.tag, Equals('Assets'))
