import sys
from setuptools import setup

from pymake.pymake import __version__

# trap installing pymake with something other than python 3
if not sys.version_info[0] in (3,):
    print('pymake not supported in your Python version')
    print('  Supported versions: 3')
    print('  Your version of Python: {}'.format(sys.version_info[0]))
    sys.exit(1)  # return non-zero value for failure

setup(name='pymake',
      description='pymake is a Python package to compile MODFLOW-based models.',
      long_description='...TO DO...',
      author='Joseph D. Hughes',
      author_email='jdhughes@usgs.gov',
      url='https://github.com/modflowpy/pymake.git',
      license='New BSD',
      platforms='Windows, Mac OS-X, Linux',
      install_requires=['numpy', 'requests'],  # numpy required for autotest functionality
      packages=['pymake'],
      include_package_data=True,
      version=__version__)
