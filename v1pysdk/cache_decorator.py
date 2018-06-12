
def key_by_args_kw(old_f, args, kw, cache_data):
  'Function to build a cache key for the cached_by_keyfunc decorator. '
  'This one just caches based on the function call arguments. i.e. Memoize '
  return repr((args, kw))


def cached_by_keyfunc(keyfunc):
  """Calls keyfunc with (old_f, args, kw, datadict) to get cache key """
  def decorator(old_f):
    data = {}
    def new_f(self, *args, **kw):
      new_key = keyfunc(old_f, args, kw, data)
      if new_key in data:
        return data[new_key]
      new_value = old_f(self, *args, **kw)
      data[new_key] = new_value
      return new_value
    return new_f
  return decorator


memoized = cached_by_keyfunc(key_by_args_kw)


