"""pymake is a python package for building MODFLOW-based and other Fortran, C,
and C++ programs. The package downloads the source files a target is released
with and builds it with the meson build system, using the build file the target
provides where there is one and writing one where there is not. The source
files a generated build file lists are ordered with a directed acyclic graph of
the module dependencies. A GNU makefile can be written for a target as well.
"""

# pymake
from .config import (
    __author__,
    __date__,
    __description__,
    __email__,
    __maintainer__,
    __status__,
    __version__,
)

# plot
from .plot.dependency_graphs import make_plots, to_pydot
from .pymake import Pymake
from .pymake_base import get_temporary_directories, main
from .pymake_build_apps import build_apps
from .pymake_parser import parser
from .utils._compiler_switches import linker_update_environment
from .utils._meson_build import meson_build, meson_install, meson_setup
from .utils.download import (
    download_and_unzip,
    get_repo_assets,
    getmfexes,
    getmfnightly,
    repo_latest_version,
    zip_all,
)

# utilities
from .utils.usgsprograms import usgs_program_data

# define public interfaces
__all__ = [
    "Pymake",
    "main",
    "parser",
    "build_apps",
    "get_temporary_directories",
    # package metadata
    "__author__",
    "__date__",
    "__description__",
    "__email__",
    "__maintainer__",
    "__status__",
    "__version__",
    # utilities
    "usgs_program_data",
    "download_and_unzip",
    "getmfexes",
    "getmfnightly",
    "repo_latest_version",
    "get_repo_assets",
    "zip_all",
    "linker_update_environment",
    # meson
    "meson_build",
    "meson_install",
    "meson_setup",
    # plot
    "make_plots",
    "to_pydot",
]
