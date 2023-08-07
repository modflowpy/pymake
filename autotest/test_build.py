import os
import sys
import time

import pytest
from flaky import flaky
from modflow_devtools.misc import set_dir

import pymake

RERUNS = 3

targets = pymake.usgs_program_data.get_keys(current=True)
targets_make = [
    t
    for t in targets
    if t not in ("libmf6", "gridgen", "mf2000", "swtv4", "mflgr")
]


def build_with_makefile(target, path, fc):
    success = True
    with set_dir(path):
        if os.path.isfile("makefile"):
            # wait to delete on windows
            if sys.platform.lower() == "win32":
                time.sleep(6)

            # clean prior to make
            print(f"clean {target} with makefile")
            os.system("make clean")

            # build MODFLOW-NWT with makefile
            print(f"build {target} with makefile")
            return_code = os.system("make")

            # test if running on Windows with ifort, if True the makefile
            # should fail
            errmsg = f"{target} created by makefile does not exist."
            if sys.platform.lower() == "win32" and fc == "ifort":
                if return_code != 0:
                    success = True
                else:
                    success = False
            # verify that MODFLOW-NWT was made
            else:
                success = os.path.isfile(target)
        else:
            errmsg = "makefile does not exist"

    return success, errmsg


@pytest.mark.base
@flaky(max_runs=RERUNS)
@pytest.mark.parametrize("target", targets)
def test_build(function_tmpdir, target: str) -> None:
    with set_dir(function_tmpdir):
        assert (
            pymake.build_apps(
                target,
                verbose=True,
                clean=False,
            )
            == 0
        ), f"could not compile {target}"


@pytest.mark.base
@flaky(max_runs=RERUNS)
# @pytest.mark.skipif(sys.platform == "win32", reason="do not run on Windows")
@pytest.mark.parametrize("target", targets)
def test_meson_build(function_tmpdir, target: str) -> None:
    with set_dir(function_tmpdir):
        assert (
            pymake.build_apps(
                target,
                verbose=True,
                clean=False,
                meson=True,
            )
            == 0
        ), f"could not compile {target}"


@pytest.mark.base
@flaky(max_runs=RERUNS)
@pytest.mark.skipif(sys.platform == "win32", reason="do not run on Windows")
@pytest.mark.parametrize("target", targets_make)
def test_makefile_build(function_tmpdir, target: str) -> None:
    pm = pymake.Pymake(verbose=True)
    pm.target = target
    pm.makefile = True
    pm.makefiledir = "."
    pm.inplace = True
    pm.dryrun = True
    pm.makeclean = False

    with set_dir(function_tmpdir):
        pm.download_target(target)
        assert pm.download, f"could not download {target} distribution"
        assert pm.build() == 0, f"could not compile {target}"

    success, errmsg = build_with_makefile(target, function_tmpdir, pm.fc)
    assert success, errmsg
