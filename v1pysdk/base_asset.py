
from pprint import pformat as pf

from query import V1Query

class BaseAsset(object):
  """Provides common methods for the dynamically derived asset type classes
     built by V1Meta.asset_class"""
    
  @classmethod
  def query(Class, where=None, sel=None):
    'Takes a V1 Data query string and returns an iterable of all matching items'
    return V1Query(Class, sel, where)
    
  @classmethod
  def select(Class, *selectlist):
    return V1Query(Class).select(*selectlist)
  
  @classmethod
  def where(Class, **wherekw):
    return V1Query(Class).where(**wherekw)
    
  @classmethod
  def filter(Class, filterexpr):
      return V1Query(Class).filter(filterexpr)
    
  @classmethod
  def asof(Class, *asofs):
      return V1Query(Class).asof(*asofs)

  @classmethod
  def from_query_select(Class, xml, asof=None):
    "Find or instantiate an object and fill it with data that just came back from query"
    idref = xml.get('id')
    data = Class._v1_v1meta.unpack_asset(xml)
    instance = Class._v1_v1meta.asset_from_oid(idref)
    instance.AsOf = asof
    data['AsOf'] = asof
    return instance.with_data(data)

  @classmethod
  def create(Class, **newdata):
    "create new asset on server and return created asset proxy instance"
    return Class._v1_v1meta.create_asset(Class._v1_asset_type_name, newdata)

  class IterableType(type):
    def __iter__(Class):
        for instance in Class.query():
            instance.needs_refresh = True
            yield instance
              
  "The type that's instantiated to make THIS class must have an __iter__, " 
  "so we provide a metaclass (a thing that provides a class when instantiated) "
  "that knows how to be iterated over, so we can say list(v1.Story)"
  __metaclass__ = IterableType
              
  def __new__(Class, oid):
    "Tries to get an instance out of the cache first, otherwise creates one"
    cache_key = (Class._v1_asset_type_name, int(oid))
    cache = Class._v1_v1meta.global_cache
    self = cache.get(cache_key, None)
    if self is None:
      self = object.__new__(Class)
      self._v1_oid = oid
      self._v1_new_data = {}
      self._v1_current_data = {}
      self._v1_needs_refresh = True
      cache[cache_key] = self
    return self

  @property
  def intid(self):
      return self._v1_oid

  @property
  def data(self):
      return self._v1_current_data

  def __getitem__(self, key):
      return self._v1_current_data[key]

  @property
  def idref(self):
    return self._v1_asset_type_name + ':' + str(self._v1_oid)
    
  @property
  def reprref(self):
      return "{0}({1})".format(self._v1_asset_type_name, self._v1_oid)
    
  @property
  def url(self):
      return self._v1_v1meta.server.build_url('/assetdetail.v1', query={'oid':self.idref})

  class ReprDummy:
      def __init__(self, value):
          self.value = value
      def __repr__(self):
          return self.value.reprref

  def repr_dummy(self, v):
      if isinstance(v, list):
          return [self.ReprDummy(item) if isinstance(item, BaseAsset) else item 
                  for item in v]
      elif isinstance(v, BaseAsset):
          return self.ReprDummy(v)          
      else:
          return v
          
  def repr_shallow(self, d):
      # patch up the dict that pformat sees to avoid repr loops
      return pf( dict(
                   (k, self.repr_dummy(v))
                   for (k,v) 
                   in d.items() 
                   if v
                 )
             )
          
  def __repr__(self):
    out = self.reprref
    shallowdata = self.repr_shallow(self._v1_current_data)
    if shallowdata != '{}':
        out += '.with_data({0})'.format(shallowdata)
    shallownew = self.repr_shallow(self._v1_new_data)
    if shallownew != '{}':
      out += '.pending({0})'.format(shallownew)
    return out
    
  def _v1_getattr(self, attr):
    "Intercept access to missing attribute names. "
    "first return uncommitted data, then refresh if needed, then get single attr, else fail"
    if self._v1_new_data.has_key(attr):
      value = self._v1_new_data[attr]
    else:
      if self._v1_needs_refresh:
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
      
  def set(self, **kw):
      self.pending(kw)
      return self

  def with_data(self, newdata):
    "bulk-set instance data"
    self._v1_current_data.update(dict(newdata))
    self._v1_needs_refresh = False
    return self
    
  def pending(self, newdata):
    "bulk-set data to commit"
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
    result = self._v1_v1meta.execute_operation(self._v1_asset_type_name, self._v1_oid, opname)
    self._v1_needs_refresh = True
    return result

