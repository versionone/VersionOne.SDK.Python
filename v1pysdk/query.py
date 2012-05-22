
from urllib import urlencode

class V1Query(object):
  """A fluent query object. Use .select() and .where() to add items to the
  select list and the query criteria, then iterate over the object to execute
  and use the query results."""
  
  def __init__(self, asset_class, sel_string=None, where_string=None):
    "Takes the asset class we will be querying"
    self.asset_class = asset_class
    self.where_terms = {}
    self.sel_list = []
    self.query_has_run = False
    self.sel_string = sel_string
    if sel_string is not None:
        self.empty_sel = False    
    self.where_string = where_string
    
  def __iter__(self):
    "Iterate over the results."
    if not self.query_has_run:
      self.run_query()
    for found_asset in self.query_results.findall('Asset'):
      yield self.asset_class.from_query_select(found_asset)
      
  def get_sel_string(self):
      if self.sel_string:
          return self.sel_string
      return ','.join(self.sel_list)

  def get_where_string(self):
      if self.where_string:
          return self.where_string
      return ';'.join("{0}='{1}'".format(attrname, criteria) for attrname, criteria in self.where_terms.items())
      
  def run_query(self):
    "Actually hit the server to perform the query"
    url_params = {}
    if self.get_sel_string() or self.empty_sel:
      url_params['sel'] = self.get_sel_string()
    if self.get_where_string():
      url_params['where'] = self.get_where_string()
    urlquery = urlencode(url_params)    
    urlpath = '/rest-1.v1/Data/{0}'.format(self.asset_class._v1_asset_type_name)
    # warning: tight coupling ahead
    xml = self.asset_class._v1_v1meta.server.get_xml(urlpath, query=urlquery)
    self.query_results = xml
    self.query_has_run = True
    return xml
    
  def select(self, *args, **kw):
    """Add attribute names to the select list for this query. The attributes
    in the select list will be returned in the query results, and can be used
    without further network traffic"""
    self.sel_list.extend(args)
    return self
    
  def where(self, *args, **kw):
    """Add where terms to the criteria for this query. Right now this method
    only allows Equals comparisons."""
    self.where_terms.update(kw)
    return self
    
  def first(self):
    return list(self)[0]
    
  def set(self, **updatelist):
    for found_asset in self:
      found_asset.pending(updatelist)
      
  def __getattr__(self, attrname):
    "return a sequence of the attribute from all matched results "
    return (getattr(i, attrname) for i in self)

