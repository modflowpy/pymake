import os
import sys

import flopy
import pytest
from flaky import flaky

import pymake

RERUNS = 3


@pytest.mark.base
@flaky(max_runs=RERUNS)
def test_pymake_makefile(function_tmpdir):
    target = "triangle"
    pm = pymake.Pymake(verbose=True)
    pm.makefile = True
    pm.makeclean = True

    if sys.platform.lower() == "win32":
        if pm.cc == "icl":
            return
        target += ".exe"

    # get current directory
    cwd = os.getcwd()

    # change to working directory so triangle download directory is
    # a subdirectory in the working directory
    os.chdir(function_tmpdir)

    # build triangle and makefile
    assert (
        pymake.build_apps(target, clean=False, pymake_object=pm) == 0
    ), f"could not build {target}"

    if (function_tmpdir / "makefile").is_file():
        print("cleaning with GNU make")
        # clean prior to make
        print(f"clean {target} with makefile")
        success, buff = flopy.run_model(
            "make",
            None,
            cargs="clean",
            model_ws=function_tmpdir,
            report=True,
            normal_msg="rm -rf ./triangle",
            silent=False,
        )

        # build triangle with makefile
        if success:
            print(f"build {target} with makefile")
            success, buff = flopy.run_model(
                "make",
                None,
                model_ws=function_tmpdir,
                report=True,
                normal_msg="cc -O2 -o triangle ./obj_temp/triangle.o",
                silent=False,
            )

    # finalize Pymake object
    pm.finalize()

    # return to starting directory
    os.chdir(cwd)

    assert (
        function_tmpdir / target
    ).is_file(), f"could not build {target} with makefile"

    return
