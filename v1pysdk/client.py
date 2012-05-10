

from urllib2 import Request, urlopen, HTTPError
import logging, time, base64

from urlparse import urlunparse

from elementtree import ElementTree


def http_get(url, username='', password=''):
  "Do an HTTP Get with optional Basic authorization"
  request = Request(url)
  if username:
    auth_string = base64.encodestring(username + ':' + password).replace('\n', '')
    request.add_header('Authorization', 'Basic ' + auth_string)
    #request.add_header('Accept', 'application/xml,application/xhtml+xml,text/html')
  t0 = time.time()
  response = urlopen(request)
  t1 = time.time()
  #print('\n\nServer RTT: %0.4f'%(t1-t0,))
  return response



class V1Error(Exception): pass

class V1AssetNotFoundError(V1Error): pass


class V1Server(object):
  "Accesses a V1 HTTP server as a client of the XML API protocol"
  
  def __init__(self, address='localhost', instance='VersionOne.Web', username='', password=''):
    self.address = address
    self.instance = instance    
    self.username = username
    self.password = password
    
  def build_url(self, path, query='', fragment='', params='', port=80):
    path = self.instance + path
    if isinstance(query, dict):
      query = urllib.urlencode(query)
    url = urlunparse( ('http', self.address, path, params, query, fragment) )
    return url
    
  def get(self, path):
    url = self.build_url(path)
    #print "\n\nUrl: ", url
    try:
      response = http_get(url, self.username, self.password)
      body = response.read()
      return (None, body)
    except HTTPError, e:
      body = e.fp.read()
      return (e, body)
      
  def get_xml(self, path):
    exception, body = self.get(path)
    document = ElementTree.fromstring(body)
    if exception:
      exception.xmldoc = document
      if exception.code == '404':
        raise V1AssetNotFoundError(exception)
      else:
        raise V1Error(exception)
    return document
   
  def get_asset_xml(self, asset_type_name, oid):
    path = '/rest-1.v1/Data/{0}/{1}'.format(asset_type_name, oid)
    return self.get_xml(path)
    

      
      
      
  
      
    
    
    
    


