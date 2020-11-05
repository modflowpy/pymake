import os
import sys
import codecs
from setuptools import setup


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), "r") as file_handle:
        return file_handle.read()


def get_constant(rel_path, tag):
    for line in read(rel_path).splitlines():
        if line.startswith(tag):
            delimiter = '"' if '"' in line else "'"
            return line.split(delimiter)[1]

    # tag not found - raise exception
    raise RuntimeError("Unable to find {} string.".format(tag))


# trap installing pymake with something other than python 3
if not sys.version_info[0] in (3,):
    print("pymake not supported in your Python version")
    print("  Supported versions: 3")
    print("  Your version of Python: {}".format(sys.version_info[0]))
    sys.exit(1)  # return non-zero value for failure

config_pth = os.path.join("pymake", "config.py")

setup(
    name="pymake",
    description="pymake is a Python package to compile MODFLOW-based models.",
    long_description=get_constant(config_pth, "__description__"),
    author="Joseph D. Hughes",
    author_email="jdhughes@usgs.gov",
    url="https://github.com/modflowpy/pymake.git",
    license="New BSD",
    platforms="Windows, Mac OS-X, Linux",
    install_requires=[
        "numpy",
        "requests",
    ],  # numpy required for autotest functionality
    packages=["pymake", "pymake.utils", "pymake.plot", "pymake.autotest"],
    include_package_data=True,
    version=get_constant(config_pth, "__version__"),
)
