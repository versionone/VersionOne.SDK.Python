
import urllib
import yaml

def encode_v1_whereterm(input):
    return input.replace("'", "''").replace('"', '""')

def single_or_list(input, separator=','):
    if isinstance(input, list):
        return separator.join(input)
    else:
        return str(input)

def where_terms(data):
    if data.has_key("where"):
        for attrname, value in data['where'].items(): 
            yield("%s='%s'"%(attrname, encode_v1_whereterm(value)))

    if data.has_key("filter"):
        filter = data['filter']
        if isinstance(filter, list):
          for term in filter:
            yield(term)
        else:
          yield(filter)

def query_params(data):
    wherestring = ';'.join(where_terms(data))
    if wherestring:
        yield('where', wherestring)

    if data.has_key("select"):
        yield('sel', single_or_list(data['select']))

    if data.has_key('asof'):
        yield('asof', data['asof'])

    if data.has_key('sort'):
        yield('sort', single_or_list(data['sort']))

    if data.has_key('page'):
        yield('page', "%(size)d,%(start)d"%data['page'])

    if data.has_key('find'):
        yield('find', data['find'])

    if data.has_key('findin'):
        yield('findin', single_or_list(data['findin']))

    if data.has_key('op'):
        yield('op', data['op'])  


def query_from_yaml(yamlstring):
    data = yaml.load(yamlstring)
    if data and data.has_key('from'):
        path = '/' + urllib.quote(data['from'])
        url = path + '?' + urllib.urlencode(list(query_params(data)))
        return url
    raise Exception("Invalid yaml output: " + str(data))



code = """
  from: Story
  select:
    - Scope.Name
    - Name
    - Estimate
    - CreateDateUTC
    - Owner[OwnedWorkitems.@Count<'']
  where:
    SuperMeAndUp.Name: All Projects
  filter:
    - Estimate>='5'
  asof: 2012-01-01 01:01:01
  sort:
    - +Name
    - -Estimate
  page:
    size: 100
    start: 0
  find: Joe
  findin:
    - Name
    - Description
  op: Delete
"""

print query_from_yaml(code)

