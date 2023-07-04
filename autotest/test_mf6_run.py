import os

import flopy
import pytest
from flaky import flaky

import pymake
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
    sim_dirs = [line for line in lines if len(line) > 0]
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
@pytest.mark.parametrize("ws", sim_dirs)
def test_mf6_run(ws):
    exe = get_pymake_appdir() / f"{target}"
    assert run_mf6(exe, ws), f"could not run {ws}"
