from v1pysdk import V1Meta


v1 = V1Meta()


for t in v1.AssetType.select('Name').where(Name='Story'):
    print t


for s in v1.Story.select('Name'):
    print s.CreateDate  # fetched on demand
    print s.Name



