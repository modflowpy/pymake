import os
import shutil
import sys

import flopy
import pytest

import pymake

# use the line below to set fortran compiler using environmental variables
# if sys.platform.lower() == "win32":
#     os.environ["CC"] = "icl"
# else:
#     os.environ["CC"] = "icc"

# working directory
cpth = os.path.abspath(os.path.join("temp", "t013"))


@pytest.mark.base
@pytest.mark.regression
def test_pymake_makefile():
    os.makedirs(cpth, exist_ok=True)

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
    os.chdir(cpth)

    # build triangle and makefile
    assert (
        pymake.build_apps(target, clean=False, pymake_object=pm) == 0
    ), f"could not build {target}"

    if os.path.isfile(os.path.join(cpth, "makefile")):
        print("cleaning with GNU make")
        # clean prior to make
        print(f"clean {target} with makefile")
        success, buff = flopy.run_model(
            "make",
            None,
            cargs="clean",
            model_ws=cpth,
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
                model_ws=cpth,
                report=True,
                normal_msg="cc -O2 -o triangle ./obj_temp/triangle.o",
                silent=False,
            )

    # finalize Pymake object
    pm.finalize()

    # return to starting directory
    os.chdir(cwd)

    assert os.path.isfile(
        os.path.join(cpth, target)
    ), f"could not build {target} with makefile"

    return


@pytest.mark.base
@pytest.mark.regression
def test_clean_up():
    shutil.rmtree(cpth)


if __name__ == "__main__":
    test_pymake_makefile()
    test_clean_up()
