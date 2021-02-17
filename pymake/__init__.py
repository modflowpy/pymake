"""pymake is a python package for compiling MODFLOW-based and other Fortran, C,
and  C++ programs. The package determines the build order using a directed
acyclic graph and then compiles the source files using GNU compilers
(:code:`gcc`, :code:`g++`, :code:`gfortran`) or Intel compilers
(:code:`ifort`, :code:`icc`)."""


# pymake
from .config import (
    __version__,
    __description__,
    __author__,
    __email__,
    __status__,
    __maintainer__,
    __date__,
)
from .pymake import Pymake
from .pymake_base import main
from .pymake_parser import parser
from .pymake_build_apps import build_apps

# autotest
from .autotest.autotest import (
    setup,
    setup_comparison,
    teardown,
    get_namefiles,
    get_entries_from_namefile,
    get_sim_name,
    get_input_files,
    compare_budget,
    compare_swrbudget,
    compare_heads,
    compare_concs,
    compare_stages,
    compare,
    setup_mf6,
    setup_mf6_comparison,
    get_mf6_comparison,
    get_mf6_files,
    get_mf6_blockdata,
    get_mf6_ftypes,
    get_mf6_mshape,
    get_mf6_nper,
)

# utilities
from .utils.usgsprograms import usgs_program_data
from .utils.download import (
    download_and_unzip,
    getmfexes,
    getmfnightly,
    repo_latest_version,
    get_repo_assets,
    zip_all,
)

# plot
from .plot.dependency_graphs import make_plots, to_pydot

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
