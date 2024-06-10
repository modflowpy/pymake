import os
import sys
from pathlib import Path
from platform import system
from typing import List

import pytest
from modflow_devtools.ostags import get_binary_suffixes

import pymake


@pytest.fixture(scope="module")
def targets() -> List[Path]:
    target = "mf6"
    ext, shared_ext = get_binary_suffixes()
    executables = [target, "zbud6", "mf5to6", "libmf6"]
    for idx, _ in enumerate(executables[:3]):
        executables[idx] += ext
    executables[3] += shared_ext
    return executables


@pytest.fixture(scope="module")
def prog_data(targets) -> dict:
    return pymake.usgs_program_data.get_target(targets[0])


@pytest.fixture(scope="module")
def workspace(module_tmpdir, prog_data) -> Path:
    return module_tmpdir / prog_data.dirname


@pytest.fixture(scope="module")
def pm(workspace, targets) -> pymake.Pymake:
    pm = pymake.Pymake(verbose=True)
    pm.target = str(targets[0])
    pm.appdir = str(workspace / "bin")
    pm.fc = os.environ.get("FC", "gfortran")
    # if system() == "Darwin" and pm.fc == "gfortran":
    #     pm.syslibs = "-Wl,-ld_classic"
    pm.meson = True
    pm.makeclean = True
    pm.mesondir = str(workspace)
    pm.verbose = True
    yield pm
    pm.finalize()


@pytest.mark.base
def test_build_with_existing_meson(pm, module_tmpdir, workspace, targets):
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

    # download modflow 6
    pm.download_target(targets[0], download_path=module_tmpdir)
    assert pm.download, f"could not download {targets[0]} distribution"

    # make modflow 6 with existing meson.build file
    returncode = pymake.meson_build(
        workspace,
        fc,
        cc,
        appdir=pm.appdir,
    )
    assert (
        returncode == 0
    ), "could not build modflow 6 applications using existing meson.build file"

    # check that all of the executables exist
    for executable in targets:
        exe_pth = os.path.join(pm.appdir, executable)
        assert os.path.isfile(exe_pth), f"{exe_pth} does not exist"
