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
      author='Christian D. Langevin',
      author_email='langevin@usgs.gov',
      url='https://github.com/modflowpy/pymake.git',
      license='New BSD',
      platforms='Windows, Mac OS-X, Linux',
      install_requires=[],  # ['pydotplus>=2.0'],
      packages=['pymake'],
      include_package_data=True,
      version=__version__)
