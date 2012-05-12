from v1pysdk import V1Meta


v1 = V1Meta()


for t in v1.AssetType.select('Name').where(Name='Story'):
    print t.Name


for s in v1.Story.select('Name'):
    print s.CreateDate
    print s.Name



