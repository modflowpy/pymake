import os
import sys

import flopy
import pytest
from flaky import flaky

from autotest.conftest import get_pymake_appdir

RERUNS = 3

# define program data
target = "mf6"


# set fpth based on current path
if os.path.basename(os.path.normpath(os.getcwd())) == "autotest":
    fpth = os.path.abspath(
        os.path.join("temp", "mf6examples", "mf6examples.txt")
    )
else:
    fpth = os.path.abspath(
        os.path.join("autotest", "temp", "mf6examples", "mf6examples.txt")
    )
if os.path.isfile(fpth):
    with open(fpth) as f:
        lines = f.read().splitlines()
    sim_dirs_gwf = [line for line in lines if len(line) > 0 and "gwf" in line]
    sim_dirs_gwt = [line for line in lines if len(line) > 0 and "gwt" in line]
    sim_dirs = sim_dirs_gwf + sim_dirs_gwt
else:
    sim_dirs = []


def run_mf6(exe, workspace):
    success = False
    exe = os.path.abspath(exe)
    if os.path.exists(exe):
        # run test models
        print(f"running model...{os.path.basename(workspace)}")
        success, buff = flopy.run_model(
            exe, None, model_ws=workspace, silent=False
        )
    return success


@pytest.mark.regression
@flaky(max_runs=RERUNS)
@pytest.mark.skipif(sys.platform == "win32", reason="do not run on Windows")
@pytest.mark.parametrize("ws", sim_dirs)
def test_mf6_run(ws):
    exe = get_pymake_appdir() / f"{target}"
    assert run_mf6(exe, ws), f"could not run {ws}"
