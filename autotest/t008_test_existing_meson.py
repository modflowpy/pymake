import contextlib
import os
import shutil
import sys
import time

import flopy
import pytest

import pymake

# set up paths
dstpth = os.path.join(f"temp_{os.path.basename(__file__).replace('.py', '')}")
if not os.path.exists(dstpth):
    os.makedirs(dstpth, exist_ok=True)

mesondir = os.path.join(dstpth, "modflow6-develop")


def clean_up():
    print("Removing temporary build directories")
    dirs_temp = [dstpth]
    for d in dirs_temp:
        if os.path.isdir(d):
            shutil.rmtree(d)
    return


@pytest.mark.base
@pytest.mark.regression
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

    # download modflow6 github repo
    url = (
        "https://github.com/MODFLOW-USGS/"
        + "modflow6/archive/refs/heads/develop.zip"
    )
    success = pymake.download_and_unzip(
        url,
        pth=dstpth,
    )
    assert success, f"could not download modflow 6 from '{url}'"

    # make modflow 6 with existing meson.build file
    returncode = pymake.meson_build(
        mesondir,
        fc,
        cc,
        appdir=os.path.join(mesondir, "bin"),
    )
    assert (
        returncode == 0
    ), "could not build modflow 6 using existing meson.build file"

    # clean up test files
    clean_up()


if __name__ == "__main__":
    test_build_with_existing_meson()
