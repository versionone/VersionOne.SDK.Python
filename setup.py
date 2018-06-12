
import sys
from setuptools import setup, find_packages

installation_requirements = [
    'elementtree',
    'testtools',
    'future',
    'urllib'
]

if (sys.version_info < (3,0)):
    # Python3 combines urllib2 and urlparse into urllib
    installation_requirements.append('urllib2')
    installation_requirements.append('urlparse')
    # has a different name if supporting Python3
    installation_requirements.append('python-ntlm')
else:
    installation_requirements.append('python-ntlm3')

setup(
  name = "v1pysdk",
  version = "0.4",
  description = "VersionOne API client",
  author = "Joe Koberg (VersionOne, Inc.)",
  author_email = "Joe.Koberg@versionone.com",
  license = "MIT/BSD",
  keywords = "versionone v1 api sdk",
  url = "http://github.com/mtalexan/VersionOne.SDK.Python.git",

  packages = [
    'v1pysdk-new',
    ],

  install_requires = installation_requirements,

  test_suite = "v1pysdk.tests",

  )







