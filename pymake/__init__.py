"""pymake is a python package for compiling MODFLOW-based and other Fortran, C,
and  C++ programs. The package determines the build order using a directed
acyclic graph and then compiles the source files using GNU compilers
(:code:`gcc`, :code:`g++`, :code:`gfortran`) or Intel compilers
(:code:`ifort`, :code:`icc`)."""


# autotest
from .autotest.autotest import (
    compare,
    compare_budget,
    compare_concs,
    compare_heads,
    compare_stages,
    compare_swrbudget,
    get_entries_from_namefile,
    get_input_files,
    get_mf6_blockdata,
    get_mf6_comparison,
    get_mf6_files,
    get_mf6_ftypes,
    get_mf6_mshape,
    get_mf6_nper,
    get_namefiles,
    get_sim_name,
    setup,
    setup_comparison,
    setup_mf6,
    setup_mf6_comparison,
    teardown,
)

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
    "__version__",
    "main",
    "parser",
    "build_apps",
    # utilities
    "usgs_program_data",
    "download_and_unzip",
    "getmfexes",
    "repo_latest_version",
    "get_repo_assets",
    "zip_all",
    # plot
    "make_plots",
    "to_pydot",
    # autotest
    "setup",
    "setup_comparison",
    "teardown",
    "get_namefiles",
    "get_entries_from_namefile",
    "get_sim_name",
    "get_input_files",
    "compare_budget",
    "compare_swrbudget",
    "compare_heads",
    "compare_concs",
    "compare_stages",
    "compare",
    "setup_mf6",
    "setup_mf6_comparison",
    "get_mf6_comparison",
    "get_mf6_files",
    "get_mf6_blockdata",
    "get_mf6_ftypes",
    "get_mf6_mshape",
    "get_mf6_nper",
]
