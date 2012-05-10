
from v1pysdk.v1meta import *
meta = V1Meta()
Story = meta.asset_class('Story')
s = Story('1005')

print s.Name
# 'New Story 2'
s.Owners
# [<v1pysdk.v1meta.Member object at 0x02AD9710>]
s.Scope
# <v1pysdk.v1meta.Scope object at 0x02AB2550>

