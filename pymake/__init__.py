# __init__.py
__name__ = 'pymake'
__author__ = 'Christian D. Langevin, Joseph Hughes'
from .version import __version__, __build__, __git_commit__

from .usgsprograms import usgs_program_data
from .pymake import main, parser
from .Popen_wrapper import process_Popen_initialize, process_Popen_command,\
    process_Popen_communicate, process_Popen_stdout
from .dag import order_source_files, order_c_source_files, get_f_nodelist
from .compiler_language_files import get_ordered_srcfiles
from .compiler_switches import get_optlevel, get_c_flags, get_fortran_flags, \
    get_linker_flags, set_arch, set_compiler, set_debug, set_cflags, \
    set_fflags, set_syslibs

from .download import download_and_unzip, getmfexes, \
    repo_latest_version, get_repo_assets, zip_all
from .visualize import make_plots
from .autotest import setup, setup_comparison, teardown, \
    get_namefiles, get_entries_from_namefile, \
    get_sim_name, get_input_files, \
    compare_budget, compare_swrbudget, compare_heads, compare_concs, \
    compare_stages, compare, \
    setup_mf6, setup_mf6_comparison, get_mf6_comparison, get_mf6_files
from .build_program import build_program, build_apps, build_replace, \
    set_bindir, compress_apps
