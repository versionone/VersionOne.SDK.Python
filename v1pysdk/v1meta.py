from client import *


"""
two-phase commit idea...
On first query, get moment number and get all assets for query from HISTORY 
at that moment. In other words, objects won't change over transaction.

Collect changes to objects.

Then something where you only update objects if their last moment was
the cached moment, or else you lost. 

"""


class V1Query(object):
  def __init__(self, asset_class):
    self.asset_class = asset_class
    self.where_terms = {}
    self.sel_list = []
    self.query_has_run = False
    
  def __iter__(self):
    if not self.query_has_run:
      self.run_query()
    for found_asset in self.query_results.findall('Asset'):
      idref = found_asset.get('id')
      yield self.asset_class.from_query_select(found_asset)
      
  def run_query(self):
    url_params = {}
    if self.sel_list:
      url_params['sel'] = ','.join(self.sel_list)
    if self.where_terms:
      url_params['where'] = ';'.join("{0}='{1}'".format(attrname, criteria) for attrname, criteria in self.where_terms.items())
    urlquery = urlencode(url_params)    
    urlpath = '/rest-1.v1/Data/{0}'.format(self.asset_class._v1_asset_type_name)
    # warning: tight coupling ahead
    xml = self.asset_class._v1_v1meta.server.get_xml(urlpath, query=urlquery)
    self.query_results = xml
    self.query_has_run = True
    return xml
    
  def select(self, *args, **kw):
    self.sel_list.extend(args)
    return self
    
  def where(self, *args, **kw):
    self.where_terms.update(kw)
    return self
    
  def set(self, **updatelist):
    if not self.query_has_run:
      self.run_query()
    for found_asset in self:
      found_asset.pending(updatelist)
      
      
        




class BaseAsset(object):
  """Provides common methods for the dynamically derived asset type classes
     built by V1Meta.asset_class"""
    
  @classmethod
  def query(Class, where=''):
    'Takes a V1 Data query string and returns an iterable of all matching items'
    match = Class._v1_v1meta.query(Class._v1_asset_type_name, where)
    for asset in match.findall('Asset'):
      idref = asset.get('id')
      yield Class._v1_v1meta.asset_from_oid(idref)

  @classmethod
  def select(Class, *selectlist):
    return V1Query(Class).select(*selectlist)
  
  @classmethod
  def where(Class, **wherekw):
    return V1Query(Class).where(**wherekw)

  @classmethod
  def from_query_select(Class, xml):
    "Find or instantiate an object and fill it with data that just came back from query"
    asset_type, oid = xml.get('id').split(':')
    instance = Class(oid)   
    data = Class._v1_v1meta.unpack_asset(xml)
    return instance.with_data(data)

  @classmethod
  def create(Class, *newdata):
    "create new asset on server and return created asset proxy instance"
    return Class._v1_v1meta.create_asset(Class._v1_asset_type_name, newdata)
      
  def __new__(Class, oid):
    "Tries to get an instance out of the cache first, otherwise creates one"
    cache_key = (Class._v1_asset_type_name, int(oid))
    cache = Class._v1_v1meta.global_cache
    if cache.has_key(cache_key):
      self = cache[cache_key]
    else:
      self = object.__new__(Class)
      self._v1_oid = oid
      self._v1_new_data = {}
      self._v1_current_data = {}
      self._v1_needs_refresh = True
      cache[cache_key] = self
    return self

  @property
  def idref(self):
    return self._v1_asset_type_name + ':' + str(self._v1_oid)

  def __repr__(self):
    "produce string representation"
    out = "{0}({1})".format(self._v1_asset_type_name, self._v1_oid)
    if self._v1_current_data:
      out += '.with_data({0})'.format(self._v1_current_data)
    if self._v1_new_data:
      out += '.pending({0})'.format(self._v1_new_data)
    return out
    
  def _v1_getattr(self, attr):
    "Intercept access to missing attribute names. "
    "first return uncommitted data, then refresh if needed, then get single attr, else fail"
    if self._v1_new_data.has_key(attr):
      value = self._v1_new_data[attr]
    else:
      if self._v1_needs_refresh: # and attr in self._v1_basicattrs
        self._v1_refresh()
      if attr not in self._v1_current_data.keys():
        self._v1_current_data[attr] = self._v1_get_single_attr(attr)
      value = self._v1_current_data[attr]
    return value
    
  def _v1_setattr(self, attr, value):
    'Stores a new value for later commit'
    if attr.startswith('_v1_'):
      object.__setattr__(self, attr, value)
    else:
      self._v1_new_data[attr] = value
      self._v1_v1meta.add_to_dirty_list(self)
      self._v1_needs_commit = True

  def with_data(self, newdata):
    "bulk-set instance data"
    self._v1_current_data.update(dict(newdata))
    self._v1_needs_refresh = False
    return self
    
  def pending(self, newdata):
    self._v1_new_data.update(dict(newdata))
    self._v1_v1meta.add_to_dirty_list(self)
    self._v1_needs_commit = True

  def _v1_commit(self):
    'Commits the object to the server and invalidates its sync state'
    if self._v1_needs_commit:
      self._v1_v1meta.update_asset(self._v1_asset_type_name, self._v1_oid, self._v1_new_data)
      self._v1_needs_commit = False
      self._v1_new_data = {}
      self._v1_current_data = {}
      self._v1_needs_refresh = True
    
  def _v1_refresh(self):
    'Syncs the objects from current server data'
    self._v1_current_data = self._v1_v1meta.read_asset(self._v1_asset_type_name, self._v1_oid)
    self._v1_needs_refresh = False
    
  def _v1_get_single_attr(self, attr):
    return self._v1_v1meta.get_attr(self._v1_asset_type_name, self._v1_oid, attr)
    
  def _v1_execute_operation(self, opname):
    self._v1_needs_refresh = True
    return self._v1_v1meta.execute_operation(self._v1_asset_type_name, self._v1_oid, opname)
    


    


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



from elementtree import ElementTree

class V1Meta(object):        
  def __init__(self, username='admin', password='admin'):
    self.server = V1Server(username=username, password=password)
    self.global_cache = {}
    self.dirtylist = []
    
  def __getattr__(self, attr):
    "Dynamically build asset type classes when someone tries to get attrs "
    "that we don't have."
    return self.asset_class(attr)
    
  @cached_by_keyfunc(key_by_args_kw)
  def asset_class(self, asset_type_name):
    xmldata = self.server.get_meta_xml(asset_type_name)
    class_members = {
        '_v1_v1meta': self, 
        '_v1_asset_type_name': asset_type_name,
        '_v1_asset_type_xml': xmldata,
        }
    for operation in xmldata.findall('Operation'):
      opname = operation.get('name')
      def operation_func(self, opname2=opname):
        self._v1_execute_operation(opname2)
      class_members[opname] = operation_func

    for attribute in xmldata.findall('AttributeDefinition'):
      attr = attribute.get("name")
      if attribute.get('attributetype') == 'Relation':
        if attribute.get('ismultivalue') == 'True':
          def getter(self, attr=attr):
            return self._v1_getattr(attr)
          def setter(self, value, attr=attr):
            return self._v1_setattr(attr, value)
          def deleter(self, attr=attr):
            raise NotImplementedError
        else:
          def getter(self, attr=attr):
            return self._v1_getattr(attr)[0]
          def setter(self, value, attr=attr):
            return self._v1_setattr(attr, [value])
          def deleter(self, attr=attr):
            raise NotImplementedError
      else:
          def getter(self, attr=attr):
            return self._v1_getattr(attr)
          def setter(self, value, attr=attr):
            return self._v1_setattr(attr, value)
          def deleter(self, attr=attr):
            raise NotImplementedError
            
      class_members[attr] = property(getter, setter, deleter) 
    new_asset_class = type(asset_type_name, (BaseAsset,), class_members)
    return new_asset_class
    
  def add_to_dirty_list(self, asset_instance):
    self.dirtylist.append(asset_instance)
    
  def commit(self):
    for asset in self.dirtylist:
      asset._v1_commit()
    self.dirtylist = []
    
  def generate_update_doc(self, newdata):
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
    return update_doc
    
  def create_asset(self, asset_type_name, newdata):
    update_doc = self.generate_update_doc(newdata)
    new_asset_xml = self.server.create_asset(asset_type_name,  update_doc)
    asset_type, asset_oid, asset_moment = new_asset_xml.get('id').split(':')
    return self.asset_class(asset_type)(asset_oid)
    
  def update_asset(self, asset_type_name, asset_oid, newdata):
    update_doc = self.generate_update_doc(newdata)
    return self.server.update_asset(asset_type_name, asset_oid, update_doc)
    
  def execute_operation(self, asset_type_name, oid, opname):
    return self.server.execute_operation(asset_type_name, oid, opname)
    
  def get_attr(self, asset_type_name, oid, attrname):
    xml = self.server.get_attr(asset_type_name, oid, attrname)
    dummy_asset = ElementTree.Element('Asset')
    dummy_asset.append(xml)
    return self.unpack_asset(dummy_asset)[attrname]
    
  def query(self, asset_type_name, wherestring):
    return self.server.get_query_xml(asset_type_name, wherestring)
    
  def read_asset(self, asset_type_name, asset_oid):
    xml = self.server.get_asset_xml(asset_type_name, asset_oid)
    return self.unpack_asset(xml)
    
  def unpack_asset(self, xml):
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
    instance = AssetClass(asset_id)
    return instance
    
  #type_converters = dict(
  #  Boolean = bool
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
