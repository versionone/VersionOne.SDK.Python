
import time

from v1pysdk import V1Meta

meta = V1Meta()

t0 = time.time()

all_asset_types = meta.AssetType.query()
all_queries = [meta.asset_class(type.Name).query() for type in all_asset_types] 
all_assets = [asset
              for query in all_queries
              for asset in query ]

t1 = time.time()

elapsed = t1 - t0
count = len(all_assets)

print "%d assets in %0.4fs (%0.4fs/asset)"%(count, elapsed, elapsed/count)



