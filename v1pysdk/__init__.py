

"""
The external interface for the v1pysdk package.  Right now there is only one
class, "V1Meta", which exposes the types and operations found in a specified
VersionOne server (defaulting to localhost/VersionOne.Web).
"""
import logging
logging.basicConfig(level=logging.DEBUG)

from v1meta import V1Meta
from v1poll import V1Poll

