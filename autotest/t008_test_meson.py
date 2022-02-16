import contextlib
import os
import shutil
import sys
import time

import flopy
import pytest

import pymake

# define program data
target = "mf6"
target_zbud = "zbud6"
if sys.platform.lower() == "win32":
    target += ".exe"
    target_zbud += ".exe"

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join(f"temp_{os.path.basename(__file__).replace('.py', '')}")
if not os.path.exists(dstpth):
    os.makedirs(dstpth, exist_ok=True)

mf6ver = prog_dict.version
mf6pth = os.path.join(dstpth, prog_dict.dirname)

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

pm = pymake.Pymake(verbose=True)
pm.target = target
pm.appdir = os.path.join(dstpth, "bin")
pm.inplace = True
pm.meson = True
pm.mesondir = os.path.join(dstpth)

epth = os.path.join(pm.appdir, target)


def clean_up():
    # finalize pymake object
    pm.finalize()

    if os.path.isfile(epth):
        print("Removing " + target)
        os.remove(epth)

    print("Removing temporary build directories")
    dirs_temp = [dstpth]
    for d in dirs_temp:
        if os.path.isdir(d):
            shutil.rmtree(d)
    return


def run_mf6(ws):
    success = False
    exe_name = os.path.abspath(epth)
    if os.path.exists(exe_name):
        # run test models
        print(f"running model...{os.path.basename(ws)}")
        success, buff = flopy.run_model(
            exe_name, None, model_ws=ws, silent=False
        )
    return success


@pytest.mark.base
@pytest.mark.regression
def test_download():
    # Remove the existing mf6 directory if it exists
    if os.path.isdir(mf6pth):
        shutil.rmtree(mf6pth)

    # download the modflow 6 release
    pm.download_target(target, download_path=dstpth)
    assert pm.download, f"could not download {target} distribution"


@pytest.mark.base
@pytest.mark.regression
def test_compile():
    assert pm.build() == 0, f"could not compile {target}"


@pytest.mark.regression
@pytest.mark.parametrize("ws", sim_dirs)
def test_mf6(ws):
    assert run_mf6(ws), f"could not run {ws}"


@pytest.mark.base
@pytest.mark.regression
def test_zbud():
    prog_dict = pymake.usgs_program_data.get_target(target_zbud)
    pmz = pymake.Pymake(verbose=True)
    pmz.target = target_zbud
    pmz.download_dir = os.path.join(dstpth, prog_dict.dirname)
    pmz.download_path = dstpth
    pmz.appdir = dstpth
    pmz.makeclean = True
    pmz.sharedobject = False
    pmz.inplace = True
    pmz.meson = True
    pmz.mesondir = os.path.join(dstpth, prog_dict.dirname)
    assert pmz.build() == 0, f"could not compile {pmz.target}"


@pytest.mark.base
@pytest.mark.regression
def test_clean_up():
    clean_up()


if __name__ == "__main__":
    test_download()
    test_compile()
    # for ws in sim_dirs:
    #     run_mf6(ws)
    test_zbud()
    # test_clean_up()
