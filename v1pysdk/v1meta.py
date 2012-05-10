
from client import *


"""
two-phase commit idea...
On first query, get moment number and get all assets for query from HISTORY 
at that moment. In other words, objects won't change over transaction.

Collect changes to objects.

Then something where you only update objects if their last moment was
the cached moment, or else you lost. 

"""



class BaseAsset(object):
  """
     Provides common methods for the dynamically derived asset type classes
     built by V1Meta.create_asset_proxy_class
  """

  @classmethod
  def find_by_id(Class, asset_id):
    cache_key = (Class._v1_asset_type_name, asset_id)
    cache = Class._v1_v1meta_instance.global_cache
    if cache.has_key(cache_key):
      return cache[cache_key]
    new_asset_instance = Class(asset_id)
    cache[cache_key] = new_asset_instance
    return new_asset_instance

  def __init__(self, oid):
    self._v1_oid = oid
    self._v1_new_data = {}
    self._v1_current_data = {}
    self._v1_needs_refresh = True

  def __getattr__(self, attr):
    if self._v1_needs_refresh:
      self._v1_refresh()
    if self._v1_new_data.has_key(attr):
      return self._v1_new_data[attr]
    return self._v1_current_data[attr]
    
  def __setattr__(self, attr, value):
    if attr.startswith('_v1_'):
      object.__setattr__(self, attr, value)
    else:
      self._v1_new_data[attr] = value
      self._v1_needs_commit = True


  def _v1_commit(self):
    if self._v1_needs_commit:
      self._v1_v1meta_instance.update_asset(self._v1_asset_type_name, self._v1_oid, self._v1_new_data)
    self._v1_needs_refresh = True
    
  def _v1_refresh(self):
    self._v1_current_data = self._v1_v1meta_instance.read_asset(self._v1_asset_type_name, self._v1_oid)
    self._v1_needs_refresh = False
    
  def _v1_execute_operation(self, opname):
    self._v1_v1meta_instance.execute_operation(self._v1_asset_type_name, self._v1_oid, opname)


    


def key_by_args_kw(old_f, args, kw, cache_data):
  return (args, kw)


def cached_by_keyfunc(keyfunc):
  """Calls keyfunc with (old_f, args, kw, datadict) to get cache key """
  def decorator(old_f):
    data = {'key': None, 'value': None}
    def new_f(*args, **kw):
      new_key = keyfunc(old_f, args, kw, data)
      if new_key == data['key']:
        return data['value']
      new_value = old_f(*args, **kw)
      data['value'] = new_value
      data['key'] = new_key
      return new_value
    return new_f
  return decorator




class V1Meta(object):
  def __init__(self, username='admin', password='admin'):
    self.server = V1Server(username=username, password=password)
    self.global_cache = {}
    
  def make_moment_keyfunc_for_asset_type(asset_type_name):
    def keyfunc(old_f, args, kw, data):
      self = args[0]
      return self.get_current_moment_for_asset_type(asset_type_name)
    return keyfunc
    
  #@cached_by_keyfunc(make_moment_keyfunc_for_asset_type('AssetType'))
  #def describe_assettype(self, asset_type_name):
  #  urlquery = { "Where": "Name='{0}'".format(asset_type_name) }
  #  data = self.server.get_xml("/rest.v1/Data/AssetType", query=urlquery)
  #  return self.create_asset_proxy_class(asset_type_name, data)
    
  @cached_by_keyfunc(key_by_args_kw)
  def create_asset_proxy_class(self, asset_type_name):
    xmldata = self.server.get_meta_xml(asset_type_name)
    class_members = {
        '_v1_v1meta_instance': self, 
        '_v1_asset_type_name': asset_type_name,
        '_v1_asset_type_xml': xmldata,
        }
          
    for operation in xmldata.findall('Operation'):
      opname = operation.get('name')
      def operation_func(self):
        self._v1_execute_operation(opname)
      class_members[opname] = operation_func
      
    new_asset_class = type(asset_type_name, (BaseAsset,), class_members)
    return new_asset_class
    
  def get_current_moment_for_asset_type(self, asset_type_name):
    return '0'
    
  def run_query(self, query):
    raise NotImplementedError
    
  def update_asset(self, asset_type_name, asset_oid, newdata):
    raise NotImplementedError
    
  def execute_operation(self, asset_type_name, oid, opname):
    return self.server.execute_operation(asset_type_name, oid, opname)
    
  def read_asset(self, asset_type_name, asset_oid):
    xml = self.server.get_asset_xml(asset_type_name, asset_oid)
    output = {}
    
    for attribute in xml.findall('Attribute'):
      key = attribute.get('name').replace('.','_')
      value = attribute.text
      output[key] = value

    for relation in xml.findall('Relation'):
      key = relation.get('name')
      related_asset_elements = relation.findall('Asset')
      rellist = []
      for value_element in related_asset_elements:
        relation_idref = value_element.get('idref')
        reltype, relid = relation_idref.split(':')
        valueclass = self.create_asset_proxy_class(reltype)
        value = valueclass.find_by_id(relid)        
        rellist.append(value)
      output[key] = rellist
    return output

