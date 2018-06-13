import sys

if (sys.version_info < (3,0)):
  from urllib import urlencode
else:
  from urllib.parse import urlencode

from .string_utils import split_attribute

class V1Query(object):
  """A fluent query object. Use .select() and .where() to add items to the
  select list and the query criteria, then iterate over the object to execute
  and use the query results."""
  
  def __init__(self, asset_class, sel_string=None, filterexpr=None):
    "Takes the asset class we will be querying"
    # warning: some of these are defined in C code 
    self._asset_class = asset_class
    self._where_terms = {}
    self._sel_list = []
    self._sel_string = None # cached copy of generated string from sel_list
    self._asof_list = []
    self._query_results = []
    self._query_has_run = False
    self._where_string = filterexpr
    self._page_size = None
    self._page_start = None
    self._find_string = None
    self._findIn_string = None
    self._sort_list = []
    self._sort_string = None # cached copy of generated string from sort_list
    self._length = 0
    self._max_length = 0 # total possible number
    self._dirty_query = False

    # sel_string is used when we need to query a single attribute that wasn't retrieved by default.
    # it should add to any existing select list.
    if sel_string:
      # parse the provided sel_string using our normal select calls
      self.select(sel_string.split(sep=","))

  def _run_query_if_needed(self):
    if not self._query_has_run:
      self.run_query()

  def _clear_query_results(self):
    """Clears the old query results so the query can be run again.  Allows re-use of a query without
       needing to re-create the query"""
    # don't delete old results if nothing has actually changed
    if self._dirty_query:
      self._query_results = []
      self._query_has_run = False

  def __iter__(self):
    """Iterate over the results, running the query the first time if necessary."""
    self._run_query_if_needed()
    for (result, asof) in self._query_results:
      for found_asset in result.findall('Asset'):
        yield self._asset_class.from_query_select(found_asset, asof)

  def __len__(self):
    """Determine the number of query results, running the query if necessary."""
    self._run_query_if_needed()
    return self._length

  def length(self):
    """Number of query results returned.  This is affected by the page() settings if they're included,
       and will return the lesser of pageSize and total-pageStart.
       See max_length() for a way to determine the total available responses independent of page() settings."""
    return len(self)

  def max_length(self):
    """Returns the maximum possible number of query results, independent of page() settings.
       This is the same as length() or len(self) only if pageStart=0 and pageSize=infinity."""
    self._run_query_if_needed()
    return self._max_length

  def queryAll(self):
    """Forces immediate running of the query so the caller has the option to control when the bulk read 
       query occurs rather than only getting piecemeal queries as various fields are needed."""
    self._run_query_if_needed()
    return self

  def reQueryAll(self):
    """Forces immediate re-running of the query so the caller has the option to control when the bulk read 
       query occurs rather than only getting piecemeal queries as various fields are needed.
       Also allows a query object to be re-used for cases where paging is the only thing that has changed.
    """
    self._clear_query_results()
    self._run_query_if_needed()
    return self

  def get_sel_string(self):
      if not self.sel_string:
        self.sel_string = ','.join(self._sel_list)
      return self.sel_string

  def get_sort_string(self):
      if not self._sort_string:
        self._sort_string = ','.join(self._sort_list)
      return self._sort_string

  def get_where_string(self):
      terms = list("{0}='{1}'".format(attrname, criteria) for attrname, criteria in self._where_terms.items())
      if self._where_string:
          terms.append(self._where_string)
      return ';'.join(terms)

  def get_page_size(self):
      return self._page_size

  def get_page_start(self):
      return self._page_start

  def get_find_string(self):
      return self._find_string

  def get_findIn_string(self):
      return self._findIn_string

  def run_single_query(self, url_params={}, api="Data"):
      urlquery = urlencode(url_params)
      urlpath = '/rest-1.v1/{1}/{0}'.format(self._asset_class._v1_asset_type_name, api)
      # warning: tight coupling ahead
      xml = self._asset_class._v1_v1meta.server.get_xml(urlpath, query=urlquery)
      # xml is an elementtree::Element object so query the total of items available and determine
      # the pageStart within that total set.
      total = int(xml.get('total'))
      pageStart = int(xml.get('pageStart'))
      pageSize =  int(xml.get('pageSize'))
      if pageStart >= total:
        # requested past end of total available
        self._length = 0
      elif (total - pageStart) < pageSize:
        # not enough to fill the pageSize, so length is what's left
        self._length = total - pageStart
      else:
        # pageSize can be met, so it is
        self._length = pageSize
      self._maxlength = total
      return xml

  def run_query(self):
    "Actually hit the server to perform the query"
    url_params = {}
    if self.get_sel_string():
      url_params['sel'] = self.get_sel_string()
    if self.get_where_string():
      url_params['where'] = self.get_where_string()
    if self.get_sort_string():
      url_params['sort'] = self.get_sort_string()
    if self.get_page_size():
      url_params['page'] = str(self.get_page_size())
      # only if page_size is set can we specify page start (optionally)
      if self.get_page_start():
        url_params['page'] += "," + str(self.get_page_start())
    if self.get_find_string() and self.get_findIn_string():
      url_params['find'] = self.get_find_string()
      url_params['findIn'] = self.get_findIn_string()
    if self._asof_list:
      for asof in self._asof_list:
        if asof:
          url_params['asof'] = str(asof)
          api = "Hist"
        else:
          del url_params['asof']
          api = "Data"
        xml = self.run_single_query(url_params, api=api)
        self._query_results.append((xml, asof))
    else:
      xml = self.run_single_query(url_params)
      self._query_results.append((xml, None))
    self._query_has_run = True
    self._dirty_query = False # results now match the query

  def select(self, *args, **kw):
    """Add attribute names to the select list for this query. The attributes
    in the select list will be returned in the query results, and can be used
    without further network traffic. Call with no arguments to clear select list."""

    # any calls to this invalidate our cached select string
    self.sel_string=None
    if len(args) == 0:
      if len(self._sel_list) > 0:
        self._sel_list = []
        self._dirty_query = True
    else:
      for sel in args:
        parts = split_attribute(sel)
        for i in range(1, len(parts)):
          pname = '.'.join(parts[:i])
          if pname not in self._sel_list:
            self._sel_list.append(pname)
        self._sel_list.append(sel)
        self._dirty_query = True
    return self

  def sort(self, *args, **kw):
    """Add order of fields to use for sorting.  Reverse sort on that field by prefacing with a 
    dash (e.g. '-Name'). Call with no arguments to clear sort list."""
    # Any calls to this invalidate our cached sort string
    self._sort_string=None
    if len(args) == 0:
      if len(self._sort_list) > 0:
        self._sort_list = []
        self._dirty_query = True
    else:
      for s in args:
        labelpos=s.strip()
        #if the field name is prepended with a -, strip that to determine the base field name
        if labelpos[0] == '-':
          labelpos=labelpos[1:]
        labelneg='-' + labelpos
        #only if the label in both the positive and negative sort order has never appeared before
        if not (labelpos in self._sort_list) and not (labelneg in self._sort_list):
          self._sort_list.append(s)
          self._dirty_query = True
    return self

  def where(self, terms={}, **kw):
    """Add where terms to the criteria for this query. Right now this method
    only allows Equals comparisons."""
    self._where_terms.update(terms)
    self._where_terms.update(kw)
    self._dirty_query = True
    return self

  def filter(self, filterexpr):
    self._where_string = filterexpr
    self._dirty_query = True
    return self

  def page(self, size=None, start=None):
    """Add page size to limit the number returned at a time, and optionally the offset to start the page at.
    'start' is 0 based and is the index of the first record.  
    'size' is a count of records to return.
    Both size and start are preserved between calls, but size must be specified for either to be used in
    the resulting query.
    Call with no arguments to clear a previous page setting."""
    if size and self._page_size != size:
      self._page_size = size
      self._dirty_query = True
    if start and self._page_start != start:
      self._page_start = start
      self._dirty_query = True
    if not size and not start:
      if self._page_size or self._page_start:
        self._page_size = None
        self._page_start = None
        self._dirty_query = True
    return self

  def find(self, text=None, field=None):
    """A very slow and inefficient search method run on the server size to search for text fields containing
    matches to the search text.
    Must specify a field to search on that matches one of the defined field names or the entire search 
    is ignored.
    Call with no arguments to clear previous find criteria."""
    if text and field:
      if self._find_string != str(text) or self._findIn_string != str(field):
        self._dirty_query = True  
        self._find_string = str(text)
        self._findIn_string = str(field)
    elif self._find_string or self._findIn_string:
        self._dirty_query = True
        # clear old values
        self._find_string=None
        self._findIn_string=None
    return self

  def asof(self, *asofs):
      for _asof_list in asofs:
          if isinstance(_asof_list, str):
              _asof_list = [_asof_list]
          for asof in _asof_list:
              self._asof_list.append(asof)
              self._dirty_query = True
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
    if attrname not in self._sel_list and not attrname.startswith('__'):
      self.select(attrname)
    return (getattr(i, attrname) for i in self)

