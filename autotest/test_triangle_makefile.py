import os
import sys

import flopy
import pytest

import pymake


@pytest.mark.base
def test_pymake_makefile(module_tmpdir):
    target = "triangle"
    pm = pymake.Pymake(verbose=True)
    pm.makefile = True
    pm.makeclean = True
    # pm.cc = "gcc"

    if sys.platform.lower() == "win32":
        if pm.cc == "icl":
            return
        target += ".exe"

    # get current directory
    cwd = os.getcwd()

    # change to working directory so triangle download directory is
    # a subdirectory in the working directory
    os.chdir(module_tmpdir)

    # build triangle and makefile
    assert (
        pymake.build_apps(target, clean=False, pymake_object=pm) == 0
    ), f"could not build {target}"

    if os.path.isfile(os.path.join(module_tmpdir, "makefile")):
        print("cleaning with GNU make")
        # clean prior to make
        print(f"clean {target} with makefile")
        success, _ = flopy.run_model(
            "make",
            None,
            cargs="clean",
            model_ws=module_tmpdir,
            report=True,
            normal_msg="rm -rf ./triangle",
            silent=False,
        )

        # build triangle with makefile
        if success:
            print(f"build {target} with makefile")
            success, _ = flopy.run_model(
                "make",
                None,
                model_ws=module_tmpdir,
                report=True,
                normal_msg="cc -O2 -o triangle ./obj_temp/triangle.o",
                silent=False,
            )

    # finalize Pymake object
    pm.finalize()

    # return to starting directory
    os.chdir(cwd)

    assert os.path.isfile(
        os.path.join(module_tmpdir, target)
    ), f"could not build {target} with makefile"
