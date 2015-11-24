from urllib import urlencode
from string_utils import split_attribute

class V1Query(object):
  """A fluent query object. Use .select() and .where() to add items to the
  select list and the query criteria, then iterate over the object to execute
  and use the query results."""
  
  def __init__(self, asset_class, sel_string=None, filterexpr=None):
    "Takes the asset class we will be querying"
    self.asset_class = asset_class
    self.where_terms = {}
    self.sel_list = []
    self.asof_list = []
    self.query_results = []
    self.query_has_run = False
    self.sel_string = sel_string
    self.empty_sel = sel_string is None
    self.where_string = filterexpr
    
  def __iter__(self):
    "Iterate over the results."
    if not self.query_has_run:
      self.run_query()
    for (result, asof) in self.query_results:
      for found_asset in result.findall('Asset'):
        yield self.asset_class.from_query_select(found_asset, asof)
      
  def get_sel_string(self):
      if self.sel_string:
          return self.sel_string
      return ','.join(self.sel_list)

  def get_where_string(self):
      terms = list("{0}='{1}'".format(attrname, criteria) for attrname, criteria in self.where_terms.items())
      if self.where_string:
          terms.append(self.where_string)
      return ';'.join(terms)
            
  def run_single_query(self, url_params={}, api="Data"):
      urlquery = urlencode(url_params)
      urlpath = '/rest-1.v1/{1}/{0}'.format(self.asset_class._v1_asset_type_name, api)
      # warning: tight coupling ahead
      xml = self.asset_class._v1_v1meta.server.get_xml(urlpath, query=urlquery)
      return xml
      
  def run_query(self):
    "Actually hit the server to perform the query"
    url_params = {}
    if self.get_sel_string() or self.empty_sel:
      url_params['sel'] = self.get_sel_string()
    if self.get_where_string():
      url_params['where'] = self.get_where_string()
    if self.asof_list:
      for asof in self.asof_list:
        if asof:
          url_params['asof'] = str(asof)
          api = "Hist"
        else:
          del url_params['asof']
          api = "Data"
        xml = self.run_single_query(url_params, api=api)
        self.query_results.append((xml, asof))
    else:
      xml = self.run_single_query(url_params)
      self.query_results.append((xml, None))
    self.query_has_run = True
    
  def select(self, *args, **kw):
    """Add attribute names to the select list for this query. The attributes
    in the select list will be returned in the query results, and can be used
    without further network traffic"""
    
    for sel in args:
      parts = split_attribute(sel)
      for i in range(1, len(parts)):
        pname = '.'.join(parts[:i])
        if pname not in self.sel_list:
          self.sel_list.append(pname)
      self.sel_list.append(sel)
    return self
    
  def where(self, terms={}, **kw):
    """Add where terms to the criteria for this query. Right now this method
    only allows Equals comparisons."""
    self.where_terms.update(terms)
    self.where_terms.update(kw)
    return self
    
  def filter(self, filterexpr):
    self.where_string = filterexpr
    return self
    
  def asof(self, *asofs):
      for asof_list in asofs:
          if isinstance(asof_list, str):
              asof_list = [asof_list]
          for asof in asof_list:
              self.asof_list.append(asof)
      return self
    
  def first(self):
    return list(self)[0]
    
  def set(self, **updatelist):
    for found_asset in self:
      found_asset.pending(updatelist)
      
  def __getattr__(self, attrname):
    """ Return a sequence of the attribute from all matched results

    .. note::

       Also checks that the selected attribute does not begin with a
       double-underscore to prevent firing off queries when python
       dunder properties are checked (like `__length_hint__` via
       `PEP0424 <http://legacy.python.org/dev/peps/pep-0424/>`_).

    """
    if attrname not in self.sel_list and not attrname.startswith('__'):
      self.select(attrname)
    return (getattr(i, attrname) for i in self)

