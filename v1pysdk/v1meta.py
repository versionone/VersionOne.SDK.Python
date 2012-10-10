try:
    from xml.etree import ElementTree
except ImportError:
    from elementtree import ElementTree

from client import *
from base_asset import BaseAsset
from cache_decorator import memoized



class V1Meta(object):        
  def __init__(self, address='localhost', instance='VersionOne.Web', username='admin', password='admin'):
    self.server = V1Server(address, instance, username, password)
    self.global_cache = {}
    self.dirtylist = []
    
  def __getattr__(self, attr):
    "Dynamically build asset type classes when someone tries to get attrs "
    "that we don't have."
    return self.asset_class(attr)
    
  def __enter__(self):
    return self
  
  def __exit__(self, *args, **kw):
    self.commit()
    
  @memoized
  def asset_class(self, asset_type_name):
    xmldata = self.server.get_meta_xml(asset_type_name)
    class_members = {
        '_v1_v1meta': self, 
        '_v1_asset_type_name': asset_type_name,
        }
    for operation in xmldata.findall('Operation'):
      opname = operation.get('name')
      def operation_func(myself, opname2=opname):
        myself._v1_execute_operation(opname2)
      class_members[opname] = operation_func

    for attribute in xmldata.findall('AttributeDefinition'):
      attr = attribute.get("name")
      if attribute.get('attributetype') == 'Relation':
        if attribute.get('ismultivalue') == 'True':
          def getter(self, attr=attr):
            return self._v1_getattr(attr)
          def setter(self, value, attr=attr):
            return self._v1_setattr(attr, list(value))
          def deleter(self, attr=attr):
            raise NotImplementedError
        else:
          def getter(self, attr=attr):
            v = self._v1_getattr(attr)
            if v:
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
      errors = []   
      for asset in self.dirtylist:
          try:
              asset._v1_commit()
          except V1Error, e:
              errors.append(e)          
          self.dirtylist = []
      return errors
    
  def generate_update_doc(self, newdata):
    update_doc = Element('Asset')
    for attrname, newvalue in newdata.items():
      if isinstance(newvalue, BaseAsset):
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
    
  def query(self, asset_type_name, wherestring, selstring):
    return self.server.get_query_xml(asset_type_name, wherestring, selstring)
    
  def read_asset(self, asset_type_name, asset_oid):
    xml = self.server.get_asset_xml(asset_type_name, asset_oid)
    return self.unpack_asset(xml)
    
  def unpack_asset(self, xml):
    output = {}
    for attribute in xml.findall('Attribute'):
      #key = attribute.get('name').replace('.','_')
      key = attribute.get('name')
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
    asset_type, asset_id = oidtoken.split(':')[:2]
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
