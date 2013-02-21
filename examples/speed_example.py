import time

from v1pysdk import V1Meta

meta = V1Meta()

t0 = time.time()

def process_queries(queries):
  for query in (meta.asset_class(type.Name) for type in meta.AssetType):
    for asset in query:
        try:
          asset._v1_refresh()
          yield str(asset)
        except Exception as e:
          yield 'Error! %s(%s)'%(asset._v1_asset_type_name, asset._v1_oid)

all_assets = list(process_queries())

t1 = time.time()

elapsed = t1 - t0
count = len(all_assets)

print("%d assets in %0.4fs (%0.4fs/asset)"%(count, elapsed, elapsed/count))

out = open('output.txt', 'w').write('\n'.join([str(a) for a in all_assets]))


