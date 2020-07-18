# __init__.py
from .pymake import Pymake, __version__
from .usgsprograms import usgs_program_data
from .pymake_base import main, parser
from .build_apps import build_apps
from .download import (
    download_and_unzip,
    getmfexes,
    repo_latest_version,
    get_repo_assets,
    zip_all,
)
from .visualize import make_plots
from .autotest import (
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
)
