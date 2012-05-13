

from urllib2 import Request, urlopen, HTTPError
from urllib import urlencode

import logging, time, base64

from urlparse import urlunparse

from elementtree import ElementTree


def http_get(url, username='', password=''):
  "Do an HTTP Get with optional Basic authorization"
  request = Request(url)
  if username:
    auth_string = base64.encodestring(username + ':' + password).replace('\n', '')
    request.add_header('Authorization', 'Basic ' + auth_string)
  response = urlopen(request)
  return response

def http_post(url, username='', password='', data=''):
  request = Request(url, data)
  if username:
    auth_string = base64.encodestring(username + ':' + password).replace('\n', '')
    request.add_header('Authorization', 'Basic ' + auth_string)
  response = urlopen(request)
  return response
  

class V1Error(Exception): pass

class V1AssetNotFoundError(V1Error): pass

from elementtree import ElementTree
from elementtree.ElementTree import Element

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
      query = urlencode(query)
    url = urlunparse( ('http', self.address, path, params, query, fragment) )
    return url
    
  def get(self, path, query='', postdata=None):
    url = self.build_url(path, query=query)
    try:
      if postdata is not None:
        response = http_post(url, self.username, self.password, postdata)
      else:
        response = http_get(url, self.username, self.password)
      body = response.read()
      return (None, body)
    except HTTPError, e:
      body = e.fp.read()
      return (e, body)
      
  def get_xml(self, path, query='', postdata=None):
    exception, body = self.get(path, query=query, postdata=postdata)
    document = ElementTree.fromstring(body)
    if exception:
      exception.xmldoc = document
      if exception.code == '404':
        raise V1AssetNotFoundError(exception)
      else:
        #ElementTree.dump(exception.xmldoc)
        raise V1Error(exception)
    return document
   
  def get_asset_xml(self, asset_type_name, oid):
    path = '/rest-1.v1/Data/{0}/{1}'.format(asset_type_name, oid)
    return self.get_xml(path)
    
  def get_query_xml(self, asset_type_name, where):
    path = '/rest-1.v1/Data/{0}'.format(asset_type_name)
    whereclause = urlencode({"Where": where})
    return self.get_xml(path, query=whereclause)
    
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
    
  def update_asset(self, asset_type_name, oid, newdata):
    update_doc = Element('Asset')
    for attrname, newvalue in newdata.items():
      if hasattr(newvalue, '_v1_v1meta'):
        node = Element('Relation')
        node.set('name', attrname)
        node.set('act', 'set')
        ra = Element('Asset')
        ra.set('idref', newvalue.idref)
        node.append(ra)
      elif isinstance(newvalue, list):
        node = Element('Relation')
        node.set('name', attrname)
        for item in newvalue:
          child = Element('Asset')
          child.set('idref', item.idref)
          child.set('act', 'set')
          node.append(child)
      else:
        node = Element('Attribute')
        node.set('name', attrname)
        node.set('act', 'set')
        node.text = str(newvalue)
      update_doc.append(node)
    newdata = ElementTree.tostring(update_doc, encoding='utf-8')
    path = '/rest-1.v1/Data/{0}/{1}'.format(asset_type_name, oid)
    return self.get_xml(path, postdata=newdata)
    """
    
    {'Attribute1': 'AttributeValue',
     'Relation1': OtherAssetClassInstance,
     'MVR1': [OtherAssetClassInstance, ...],
     }
     ->
     <Asset name="Story">
     
       <Attribute name="Attribute1" act="set">AttributeValue</Attribute>
       
       <Relation name="Relation1" act="set">
         <Asset idref="Whatever:1245" />
       </Relation>
       
       <Relation name="MVR1">
         <Asset idref="Whatever:0001" act="set" />
       </Relation>
       
     </Asset>
     """

    
    

      
      
      
  
      
    
    
    
    


