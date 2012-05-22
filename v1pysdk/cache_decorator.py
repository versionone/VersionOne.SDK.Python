
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


memoized = cached_by_keyfunc(key_by_args_kw)


