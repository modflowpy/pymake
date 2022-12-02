import contextlib
import os
import shutil
import sys
import time

import flopy
import pytest

import pymake

target = "mf6"
ext = ""
shared_ext = ".so"
executables = [target, "zbud6", "mf5to6", "libmf6"]
if sys.platform.lower() == "win32":
    ext = ".exe"
    shared_ext = ".dll"
elif sys.platform.lower() == "darwin":
    shared_ext = ".dylib"
for idx, executable in enumerate(executables[:3]):
    executables[idx] += ext
executables[3] += shared_ext

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join(f"temp_{os.path.basename(__file__).replace('.py', '')}")
if not os.path.exists(dstpth):
    os.makedirs(dstpth, exist_ok=True)

mf6pth = os.path.join(dstpth, prog_dict.dirname)
mesondir = mf6pth


def clean_up():
    print("Removing temporary build directories")
    dirs_temp = [dstpth]
    for d in dirs_temp:
        if os.path.isdir(d):
            shutil.rmtree(d)
    return


@pytest.mark.base
def test_build_with_existing_meson():
    # set default compilers
    fc, cc = "gfortran", "gcc"

    # get the arguments
    for idx, arg in enumerate(sys.argv):
        if arg == "-fc":
            fc = sys.argv[idx + 1]
        elif "-fc=" in arg:
            fc = arg.split("=")[1]
        if arg == "-cc":
            cc = sys.argv[idx + 1]
        elif "-cc=" in arg:
            cc = arg.split("=")[1]

    # check if fc differs from environmental variable
    fc_env = os.environ.get("FC")
    if fc_env is not None:
        if fc != fc_env:
            fc = fc_env

    # check if cc differs from environmental variable
    cc_env = os.environ.get("CC")
    if cc_env is not None:
        if cc != cc_env:
            cc = cc_env

    # print fortran and c/c++ compilers
    print(f"fortran compiler={fc}\n" + f"c/c++ compiler={cc}\n")

    pm = pymake.Pymake(verbose=True)
    pm.target = target
    pm.appdir = os.path.join(mesondir, "bin")
    pm.meson = True
    pm.makeclean = True
    pm.mesondir = mesondir
    pm.verbose = True

    # download the modflow 6
    pm.download_target(target, download_path=dstpth)
    assert pm.download, f"could not download {target} distribution"

    # make modflow 6 with existing meson.build file
    returncode = pymake.meson_build(
        mesondir,
        fc,
        cc,
        appdir=pm.appdir,
    )
    assert (
        returncode == 0
    ), "could not build modflow 6 applications using existing meson.build file"

    # check that all of the executables exist
    for executable in executables:
        exe_pth = os.path.join(pm.appdir, executable)
        assert os.path.isfile(exe_pth), f"{exe_pth} does not exist"

    # clean up test files
    clean_up()


if __name__ == "__main__":
    test_build_with_existing_meson()
