

from urllib2 import Request, urlopen, HTTPError
import base64

from urlparse import urlunparse




def http_get(url, username='', password=''):
  "Do an HTTP Get with optional Basic authorization"
  request = Request(url)
  if username:
    auth_string = base64.encodestring(username + ':' + password).replace('\n', '')
    request.add_header('Authorization', 'Basic ' + auth_string)
    request.add_header('Accept', 'application/xml,application/xhtml+xml,text/html')
  response = urlopen(request)
  return response



class V1Server:
  "Accesses a V1 HTTP server as a client of the XML API protocol"
  
  def __init__(self, host='localhost', instance='VersionOne.Web', username='', password=''):
    self.host = host
    self.instance = instance    
    self.username = username
    self.password = password
    
  def build_url(self, path, query='', fragment='', params='', port=80):
    path = self.instance + '/' + path
    url = urlunparse( ('http', self.host, path, params, query, fragment) )
    return url
    
  def connect(self, path):
    url = self.build_url(path)
    try:
      response = http_get(url, self.username, self.password)
      return (response.code, response.read())
    except HTTPError, e:
      body = e.fp.read()
      return (e.code, e.fp.read())
      
      
      
  
      
    
    
    
    


