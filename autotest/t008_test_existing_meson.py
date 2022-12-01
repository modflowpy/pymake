import contextlib
import os
import shutil
import sys
import time
from pathlib import Path

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


@pytest.mark.base
@pytest.mark.regression
def test_build_with_existing_meson(tmpdir):
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

    mesondir = tmpdir / "mf6.3.0_linux"
    builddir = Path(mesondir / "builddir")
    builddir.mkdir(parents=True, exist_ok=True)

    pm = pymake.Pymake(verbose=True)
    pm.target = target
    pm.appdir = str(mesondir / "bin")
    pm.meson = True
    pm.makeclean = True
    pm.mesondir = str(mesondir)
    pm.verbose = True

    # download the modflow 6
    pm.download_target(target, download_path=str(tmpdir))
    assert pm.download, f"could not download {target} distribution"

    # make modflow 6 with existing meson.build file
    returncode = pymake.meson_build(
        mesondir,
        fc,
        cc,
        appdir=pm.appdir,
        build_dir=str(builddir)
    )
    assert (
        returncode == 0
    ), "could not build modflow 6 applications using existing meson.build file"

    assert len(list(mesondir.glob('*'))) > 0

    # check that all of the executables exist
    for executable in executables:
        exe_pth = os.path.join(pm.appdir, executable)
        assert os.path.isfile(exe_pth), f"{exe_pth} does not exist"


if __name__ == "__main__":
    test_build_with_existing_meson()
