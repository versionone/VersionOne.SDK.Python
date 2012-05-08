from testtools import TestCase
from testtools.matchers import Equals


from elementtree.ElementTree import parse, fromstring, ElementTree



from v1pysdk.client import *


class TestV1Connection(TestCase):
  
  def test_connect(self, username='admin', password='admin'):
    
    server = V1Server(username=username, password=password)
    
    code, body = server.connect('rest-1.v1/Data/Story')

    elem = fromstring(body)
    self.assertThat(elem.tag, Equals('Assets'))

    
    
    

