
import sys
from setuptools import setup, find_packages

install_requires = [
    'future'
]

if (sys.version_info < (3,0)):
    # has a different name if supporting Python3
    install_requires.append('python-ntlm')
else:
    install_requires.append('python-ntlm3')

setup(
  name = "v1pysdk",
  version = "0.5",
  description = "VersionOne API client",
  author = "Joe Koberg (VersionOne, Inc.)",
  author_email = "Joe.Koberg@versionone.com",
  license = "MIT/BSD",
  keywords = "versionone v1 api sdk",
  url = "http://github.com/mtalexan/VersionOne.SDK.Python.git",

  packages = [
    'v1pysdk',
    ],

  install_requires = install_requires,

  #tests don't work, so ignore them
  #tests_require = [
  #    'testtools'
  #],
  #  
  #test_suite = "v1pysdk.tests",

  )







