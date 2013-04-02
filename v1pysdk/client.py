
import logging, time, base64
import urllib2
from urllib2 import Request, urlopen, HTTPError, HTTPBasicAuthHandler
from urllib import urlencode
from urlparse import urlunparse
import httplib2

try:
    from xml.etree import ElementTree
    from xml.etree.ElementTree import Element
except ImportError:
    from elementtree import ElementTree
    from elementtree.ElementTree import Element

import oauth2client
import oauth2client.clientsecrets
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import flow_from_clientsecrets


class V1Error(Exception): pass

class V1AssetNotFoundError(V1Error): pass

class V1OAuth2Error(V1Error): pass

class V1Oauth2CredentialsError(V1OAuth2Error): pass

class V1Oauth2ClientSecretsError(V1OAuth2Error): pass


class V1Server(object):
  "Accesses a V1 HTTP server as a client of the XML API protocol"
  API_PATH="/rest-1.oauth.v1"

  def __init__(self, address='localhost', instance='VersionOne.Web', client_secrets_file="client_secrets.json", stored_credentials_file="stored_credentials.json"):
    self.address = address
    self.instance = instance
    self.creds_storage = Storage(stored_credentials_file)
    try:
      self.flow = flow_from_clientsecrets(client_secrets_file,
            scope='apiv1',
            redirect_uri='urn:ietf:wg:oauth:2.0:oob'
            )
    except oauth2client.clientsecrets.InvalidClientSecretsError:
      raise V1Oauth2ClientSecretsError("Stored client secrets file not found. Please use the command line tool to obtain it. For more information see http://docs.versionone.com/oauth2/something")
    self.httpclient = httplib2.Http()
    credentials = self.creds_storage.get()
    if not credentials:
      raise V1Oauth2CredentialsError("Stored client credentials not found. Please use the command line tool to obtain them. For more information see http://docs.versionone.com/oauth2/something")
    credentials.authorize(self.httpclient)
    logging.debug("Client has been authorized.")
    logging.debug(credentials)
    logging.debug(self.flow)

  def http_get(self, url):
    return self.httpclient.request(url, "GET")
  
  def http_post(self, url, data=''):
    return self.httpclient.request(url, 'POST', body=data)
    
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
    logging.debug(url)
    if postdata is not None:
        if isinstance(postdata, dict):
            postdata = urlencode(postdata)
        return self.http_post(url, postdata)
    return self.http_get(url)
      
  def get_xml(self, path, query='', postdata=None):
    response, body = self.fetch(path, query=query, postdata=postdata)
    document = ElementTree.fromstring(body)
    if response.status == 404:
      raise V1AssetNotFoundError(response.reason)
    elif response.status == 400:
      raise V1Error('\n'+body)
    elif response.status >= 400:
      raise V1Error(response)
    return document
   
  def get_asset_xml(self, asset_type_name, oid):
    path = self.API_PATH + '/Data/{0}/{1}'.format(asset_type_name, oid)
    return self.get_xml(path)
    
  def get_query_xml(self, asset_type_name, where=None, sel=None):
    path = self.API_PATH + '/Data/{0}'.format(asset_type_name)
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
    path = self.API_PATH + '/Data/{0}/{1}'.format(asset_type_name, oid)
    query = {'op': opname}
    return self.get_xml(path, query=query, postdata={})
    
  def get_attr(self, asset_type_name, oid, attrname):
    path = self.API_PATH + '/Data/{0}/{1}/{2}'.format(asset_type_name, oid, attrname)
    return self.get_xml(path)
  
  def create_asset(self, asset_type_name, xmldata, context_oid=''):
    body = ElementTree.tostring(xmldata, encoding="utf-8")
    query = {}
    if context_oid:
      query = {'ctx': context_oid}
    path = self.API_PATH + '/Data/{0}'.format(asset_type_name)
    return self.get_xml(path, query=query, postdata=body)
    
  def update_asset(self, asset_type_name, oid, update_doc):
    newdata = ElementTree.tostring(update_doc, encoding='utf-8')
    path = self.API_PATH + '/Data/{0}/{1}'.format(asset_type_name, oid)
    return self.get_xml(path, postdata=newdata)


  def get_attachment_blob(self, attachment_id, blobdata=None):
    path = '/attachment.v1/{0}'.format(attachment_id)
    exception, body = self.fetch(path, postdata=blobdata)
    if exception:
        raise exception
    return body
    
  set_attachment_blob = get_attachment_blob
  
    
    
  
    

