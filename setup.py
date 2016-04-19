import os
import sys
from setuptools import setup

from pymake.pymake import __version__

# trap someone trying to install pymake with something other
#  than python 2 or 3
if not sys.version_info[0] in [2, 3]:
    print('Sorry, pymake not supported in your Python version')
    print('  Supported versions: 2 and 3')
    print('  Your version of Python: {}'.format(sys.version_info[0]))
    sys.exit(1) # return non-zero value for failure


setup(name='pymake',
      description='pymake is a Python package to compile MODFLOW-based models.',
      long_description='...TO DO...',
      author='Christian D. Langevin',
      author_email='langevin@usgs.gov',
      url='https://github.com/modflowpy/pymake.git',
      license='New BSD',
      platforms='Windows, Mac OS-X',
      install_requires=[], # ['pydotplus>=2.0'],
      packages=['pymake'],
      version=__version__ )
