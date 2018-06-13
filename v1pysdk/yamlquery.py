import sys

if (sys.version_info < (3,0)):
    import urllib as theUrlLib
else:
    import urllib.parse as theUrlLib
import yaml

def encode_v1_whereterm(input):
    return input.replace("'", "''").replace('"', '""')

def single_or_list(input, separator=','):
    if isinstance(input, list):
        return separator.join(input)
    else:
        return str(input)

def where_terms(data):
    if "where" in data:
        for attrname, value in data['where'].items(): 
            yield("%s='%s'"%(attrname, encode_v1_whereterm(value)))

    if "filter" in data:
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

    if "select" in data:
        yield('sel', single_or_list(data['select']))

    if 'asof' in data:
        yield('asof', data['asof'])

    if 'sort' in data:
        yield('sort', single_or_list(data['sort']))

    if 'page' in data:
        yield('page', "%(size)d,%(start)d"%data['page'])

    if 'find' in data:
        yield('find', data['find'])

    if 'findin' in data:
        yield('findin', single_or_list(data['findin']))

    if 'op' in data:
        yield('op', data['op'])  


def query_from_yaml(yamlstring):
    data = yaml.load(yamlstring)
    if data and 'from' in data:
        path = '/' + theUrlLib.quote(data['from'])
        url = path + '?' + theUrlLib.urlencode(list(query_params(data)))
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

print(query_from_yaml(code))

