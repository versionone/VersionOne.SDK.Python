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
     built by V1Meta.asset_class
  """

  @classmethod
  def find_by_id(Class, asset_id):
    'Takes an asset id (e.g. "1004") and returns the (possibly old) instance representing it'
    cache_key = (Class._v1_asset_type_name, asset_id)
    cache = Class._v1_v1meta.global_cache
    if cache.has_key(cache_key):
      return cache[cache_key]
    new_asset_instance = Class(asset_id)
    cache[cache_key] = new_asset_instance
    return new_asset_instance
    
  @classmethod
  def query(Class, where=''):
    'Takes a V1 Data query string and returns an iterable of all matching items'
    match = Class._v1_v1meta.query(Class._v1_asset_type_name, where)
    for asset in match.findall('Asset'):
      idref = asset.get('id')
      yield Class._v1_v1meta.asset_from_oid(idref)

  @classmethod
  def create(Class, newdata):
    create_response = Class._v1_v1meta.create_asset(Class._v1_asset_type_name, newdata)
    new_oid = create_response.find('Asset').get('idref')
    return Class._v1_v1meta.asset_from_oid(new_oid)
      
  def __init__(self, oid):
    'Takes an asset id and always instantiates a new asset instance'
    self._v1_oid = oid
    self._v1_new_data = {}
    self._v1_current_data = {}
    self._v1_needs_refresh = True

  def __getattr__(self, attr):
    'Syncs up the object if needed, and preferentially returns any pending data. '
    'else returns the data read from the server at last sync.'
    if self._v1_needs_refresh:
      self._v1_refresh()
    if self._v1_new_data.has_key(attr):
      value = self._v1_new_data[attr]
    else:
      value = self._v1_current_data[attr]
    if isinstance(value, list) and attr not in self._v1_multi_valued_relations:
      if value:
        value = value[0]
      else:
        value = None
    return value
    
  def __setattr__(self, attr, value):
    'Stores a new value for later commit'
    if attr.startswith('_v1_'):
      object.__setattr__(self, attr, value)
    else:
      self._v1_new_data[attr] = value
      self._v1_needs_commit = True


  def _v1_commit(self):
    'Commits the object to the server and invalidates its sync state'
    if self._v1_needs_commit:
      self._v1_v1meta.update_asset(self._v1_asset_type_name, self._v1_oid, self._v1_new_data)
    self._v1_needs_refresh = True
    
  def _v1_refresh(self):
    'Syncs the objects from current server data'
    self._v1_current_data = self._v1_v1meta.read_asset(self._v1_asset_type_name, self._v1_oid)
    self._v1_needs_refresh = False
    
  def _v1_execute_operation(self, opname):
    self._v1_v1meta.execute_operation(self._v1_asset_type_name, self._v1_oid, opname)


    


def key_by_args_kw(old_f, args, kw, cache_data):
  'Function to build a cache key for the cached_by_keyfunc decorator. '
  'This one just caches based on the function call arguments. i.e. Memoize '
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


import iso8601

class V1Meta(object):    
  #type_converters = dict(
  #  Numeric = float,
  #  Date = iso8601.parse_date,
  #  Duration = str,
  #  Text = str,
  #  LongText = str,
  #  Relation = str,
  #  Rank = str,
  #  AssetType = str,
  #  Opaque = str,
  #  State = int,
  #  Password = str,
  #  Blob = str,
  #)
    
  def __init__(self, username='admin', password='admin'):
    self.server = V1Server(username=username, password=password)
    self.global_cache = {}
    
  def __getattr__(self, attr):
    "Dynamically build asset type classes when someone tries to get attrs "
    "that we don't have."
    return self.asset_class(attr)
    
  #def make_moment_keyfunc_for_asset_type(asset_type_name):
  #  def keyfunc(old_f, args, kw, data):
  #    self = args[0]
  #    return self.get_current_moment_for_asset_type(asset_type_name)
  #  return keyfunc
    
  #@cached_by_keyfunc(make_moment_keyfunc_for_asset_type('AssetType'))
  #def describe_assettype(self, asset_type_name):
  #  urlquery = { "Where": "Name='{0}'".format(asset_type_name) }
  #  data = self.server.get_xml("/rest.v1/Data/AssetType", query=urlquery)
  #  return self.create_asset_proxy_class(asset_type_name, data)
    
  @cached_by_keyfunc(key_by_args_kw)
  def asset_class(self, asset_type_name):
    xmldata = self.server.get_meta_xml(asset_type_name)
    mvrs = [attrdef.get('name') for attrdef in  xmldata.findall('AttributeDefinition') if attrdef.get('ismultivalue') == 'True']
    class_members = {
        '_v1_v1meta': self, 
        '_v1_asset_type_name': asset_type_name,
        '_v1_asset_type_xml': xmldata,
        '_v1_multi_valued_relations': mvrs,
        }
    for operation in xmldata.findall('Operation'):
      opname = operation.get('name')
      def operation_func(self, opname2=opname):
        self._v1_execute_operation(opname2)
      class_members[opname] = operation_func
    new_asset_class = type(asset_type_name, (BaseAsset,), class_members)
    return new_asset_class
    
  #def get_current_moment_for_asset_type(self, asset_type_name):
  #  return '0'
    
  def update_asset(self, asset_type_name, asset_oid, newdata):
    raise NotImplementedError
    
  def execute_operation(self, asset_type_name, oid, opname):
    return self.server.execute_operation(asset_type_name, oid, opname)
    
  def query(self, asset_type_name, wherestring):
    return self.server.get_query_xml(asset_type_name, wherestring)
    
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
        value = self.asset_from_oid(relation_idref)
        rellist.append(value)
      output[key] = rellist
    return output
    
  def asset_from_oid(self, oidtoken):
    asset_type, asset_id = oidtoken.split(':')
    AssetClass = self.asset_class(asset_type)
    instance = AssetClass.find_by_id(asset_id)
    return instance
    
    

    

