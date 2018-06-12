import sys

try:
    from xml.etree import ElementTree
except ImportError:
    from elementtree import ElementTree

from .client import *
from .base_asset import BaseAsset
from .cache_decorator import memoized
from .special_class_methods import special_classes
from .none_deref import NoneDeref
from .string_utils import split_attribute

class V1Meta(object):        
  def __init__(self, *args, **kw):
    self.server = V1Server(*args, **kw)
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
            else:
              return NoneDeref()
          def setter(self, value, attr=attr):
            return self._v1_setattr(attr, value)
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
      
    bases = [BaseAsset,]
    # mix in any special methods
    if asset_type_name in special_classes:
      mixin = special_classes[asset_type_name]
      bases.append(mixin)
      
    new_asset_class = type(asset_type_name, tuple(bases), class_members)
    return new_asset_class
    
  def add_to_dirty_list(self, asset_instance):
    self.dirtylist.append(asset_instance)
    
  def commit(self):
      errors = []   
      for asset in self.dirtylist:
          try:
              asset._v1_commit()
          except V1Error as e:
              errors.append(e)          
          self.dirtylist = []
      return errors
    
  def generate_update_doc(self, newdata):
    update_doc = Element('Asset')
    for attrname, newvalue in newdata.items():
      if newvalue is None: # single relation was removed
        node = Element('Relation')
        node.set('name', attrname)
        node.set('act', 'set')
      elif isinstance(newvalue, BaseAsset): # single relation was changed
        node = Element('Relation')
        node.set('name', attrname)
        node.set('act', 'set')
        ra = Element('Asset')
        ra.set('idref', newvalue.idref)
        node.append(ra)
      elif isinstance(newvalue, list): # multi relation was changed
        node = Element('Relation')
        node.set('name', attrname)
        for item in newvalue:
          child = Element('Asset')
          child.set('idref', item.idref)
          child.set('act', 'add')
          node.append(child)
      else: # Not a relation
        node = Element('Attribute')
        node.set('name', attrname)
        node.set('act', 'set')
        if ((sys.version_info >= (3,0)) and not isinstance(newvalue, str)) or ((sys.version_info < (3,0)) and isinstance(newvalue, unicode)):
            node.text = str(newvalue).decode('utf-8')
        else:
            node.text = newvalue
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
    
  def get_attr(self, asset_type_name, oid, attrname, moment=None):
    xml = self.server.get_attr(asset_type_name, oid, attrname, moment)
    dummy_asset = ElementTree.Element('Asset')
    dummy_asset.append(xml)
    return self.unpack_asset(dummy_asset)[attrname]
    
  def query(self, asset_type_name, wherestring, selstring):
    return self.server.get_query_xml(asset_type_name, wherestring, selstring)
    
  def read_asset(self, asset_type_name, asset_oid, moment=None):
    xml = self.server.get_asset_xml(asset_type_name, asset_oid, moment)
    return self.unpack_asset(xml)
    
  def unpack_asset(self, xml):
    output = {}
    self.unpack_asset_relations(output, xml)
    self.unpack_asset_attributes(output, xml)
    return output
  
  def unpack_asset_attributes(self, output, xml):
    for attribute in xml.findall('Attribute'):
      #key = attribute.get('name').replace('.','_')
      key = attribute.get('name')
      values = [v.text for v in attribute.findall('Value')]
      if len(values) == 0:
        values = [attribute.text]
      
      self.add_attribute_to_output(output, key, values)

  def unpack_asset_relations(self, output, xml):

    # we sort relations in order to insert the shortest ones first, so that
    # containing relations are added before leaf ones.
    for relation in sorted(xml.findall('Relation'), key=lambda x: x.get('name')):
      key = relation.get('name')
      related_asset_elements = relation.findall('Asset')
      rellist = []
      for value_element in related_asset_elements:
        relation_idref = value_element.get('idref')
        value = self.asset_from_oid(relation_idref)
        rellist.append(value)
      self.add_relation_to_output(output, key, rellist)

  def add_relation_to_output(self, output, relation, assets):
    if self.is_attribute_qualified(relation):
      (container, leaf) = self.split_relation_to_container_and_leaf(relation)

      asset = self.get_related_asset(output, container)

      # asset may be unset because the reference is broken
      if asset:
        asset.with_data({leaf: assets})
    else:
      output[relation] = assets

  def add_attribute_to_output(self, output, relation, values):
    if self.is_attribute_qualified(relation):
      (container, leaf) = self.split_relation_to_container_and_leaf(relation)

      for (asset, value) in zip(self.get_related_assets(output, container), values):
         # for calculated values it is not an asset so take the value directly
        if hasattr(asset, 'with_data'):
          asset.with_data({leaf: value})
        else:
          output[relation] = value
    else:
      output[relation] = values[0]
      
  def is_attribute_qualified(self, relation):
    parts = split_attribute(relation)
    return len(parts) > 1
  
  def split_relation_to_container_and_leaf(self, relation):
    parts = split_attribute(relation)
    return ('.'.join(parts[:-1]), parts[-1])
  
  def get_related_assets(self, output, relation):
    if self.is_attribute_qualified(relation):
      parts = split_attribute(relation)

      assets = output[parts[0]]

      for part in parts[1:]:
        try:
          asset = assets[0]
        except IndexError:
          return []

        assets = asset._v1_getattr(part)
      return assets
    else:
      return output[relation]
  
  def get_related_asset(self, output, relation):
    assets = self.get_related_assets(output, relation)
    try:
      return assets[0]
    except IndexError:
      return None
  
  def asset_from_oid(self, oidtoken):
    oid_parts = oidtoken.split(":")
    (asset_type, asset_id, moment) = oid_parts if len(oid_parts)>2 else (oid_parts[0], oid_parts[1], None)
    AssetClass = self.asset_class(asset_type)
    instance = AssetClass(asset_id, moment)
    return instance
    
  def set_attachment_blob(self, attachment, data=None):
     intid = attachment.intid if isinstance(attachment, BaseAsset) else attachment
     return self.server.set_attachment_blob(intid, data)
      
  get_attachment_blob = set_attachment_blob
      

  # This will eventually require iso8601 module
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
