
import logging, time, base64
import urllib2
from urllib2 import Request, urlopen, HTTPError, HTTPDigestAuthHandler
from urllib import urlencode
from urlparse import urlunparse

try:
    from xml.etree import ElementTree
    from xml.etree.ElementTree import Element
except ImportError:
    from elementtree import ElementTree
    from elementtree.ElementTree import Element

auth_handlers = [HTTPDigestAuthHandler]

try:
    from ntlm.HTTPNtlmAuthHandler import HTTPNtlmAuthHandler
    auth_handlers.append(HTTPNtlmAuthHandler)
except ImportError:
    pass

def http_get(url, username='', password=''):
  "Do an HTTP Get with optional Basic authorization"
  #print url
  request = Request(url)
  response = urlopen(request)
  return response

def http_post(url, username='', password='', data=''):
  #print url, data
  request = Request(url, data)
  if username:
    auth_string = base64.encodestring(username + ':' + password).replace('\n', '')
    request.add_header('Authorization', 'Basic ' + auth_string)
  response = urlopen(request)
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
    self._install_openers()

  def _install_openers(self):
    """Install authentication handlers for NTLM and Digest auth.
    """
    if self.username:
      base_url = self.build_url('')
      password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
      password_manager.add_password(None, base_url, self.username, self.password)
      handlers = [handler(password_manager) for handler in auth_handlers]
      opener = urllib2.build_opener(*handlers)
      urllib2.install_opener(opener)



  def build_url(self, path, query='', fragment='', params='', port=80):
    "So we dont have to interpolate urls ad-hoc"
    path = self.instance + path
    if isinstance(query, dict):
      query = urlencode(query)
    url = urlunparse( ('http', self.address, path, params, query, fragment) )
    return url
    
  def fetch(self, path, query='', postdata=None):
    "Perform an HTTP GET or POST depending on whether postdata is present"
    url = self.build_url(path, query=query)
    try:
      if postdata is not None:
          if isinstance(postdata, dict):
              postdata = urlencode(postdata)
          response = http_post(url, self.username, self.password, postdata)
      else:
        response = http_get(url, self.username, self.password)
      body = response.read()
      return (None, body)
    except HTTPError, e:
      body = e.fp.read()
      return (e, body)
      
  def get_xml(self, path, query='', postdata=None):
    exception, body = self.fetch(path, query=query, postdata=postdata)
    document = ElementTree.fromstring(body)
    if exception:
      exception.xmldoc = document
      if exception.code == 404:
        raise V1AssetNotFoundError(exception)
      elif exception.code == 400:
        raise V1Error('\n'+body)
      else:
        raise V1Error(exception)
    return document
   
  def get_asset_xml(self, asset_type_name, oid):
    path = '/rest-1.v1/Data/{0}/{1}'.format(asset_type_name, oid)
    return self.get_xml(path)
    
  def get_query_xml(self, asset_type_name, where=None, sel=None):
    path = '/rest-1.v1/Data/{0}'.format(asset_type_name)
    query = {}
    if where is not None:
        query['Where'] = where
    if sel is not None:
        query['sel'] = sel        
    return self.get_xml(path, query=query)
    
  def get_meta_xml(self, asset_type_name):
    path = '/meta.v1/{0}'.format(asset_type_name)
    return self.get_xml(path)
    
  def execute_operation(self, asset_type_name, oid, opname):
    path = '/rest-1.v1/Data/{0}/{1}'.format(asset_type_name, oid)
    query = {'op': opname}
    return self.get_xml(path, query=query, postdata={})
    
  def get_attr(self, asset_type_name, oid, attrname):
    path = '/rest-1.v1/Data/{0}/{1}/{2}'.format(asset_type_name, oid, attrname)
    return self.get_xml(path)
  
  def create_asset(self, asset_type_name, xmldata, context_oid=''):
    body = ElementTree.tostring(xmldata, encoding="utf-8")
    query = {}
    if context_oid:
      query = {'ctx': context_oid}
    path = '/rest-1.v1/Data/{0}'.format(asset_type_name)
    return self.get_xml(path, query=query, postdata=body)
    
  def update_asset(self, asset_type_name, oid, update_doc):
    newdata = ElementTree.tostring(update_doc, encoding='utf-8')
    path = '/rest-1.v1/Data/{0}/{1}'.format(asset_type_name, oid)
    return self.get_xml(path, postdata=newdata)


