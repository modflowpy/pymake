import os
import sys
import shutil
import pymake
import flopy

# working directory
cpth = os.path.abspath(os.path.join("temp", "t013"))


def test_gnu_make():
    os.makedirs(cpth, exist_ok=True)

    target = "triangle"
    pm = pymake.Pymake(verbose=True)
    pm.makefile = True
    pm.makeclean = True
    pm.cc = "gcc"

    if sys.platform.lower() == "win32":
        target += ".exe"

    # get current directory
    cwd = os.getcwd()

    # change to working directory so triangle download directory is
    # a subdirectory in the working directory
    os.chdir(cpth)

    # build triangle and makefile
    assert (
        pymake.build_apps(target, clean=False, pymake_object=pm) == 0
    ), "could not build {}".format(target)

    if os.path.isfile(os.path.join(cpth, "makefile")):
        print("cleaning with GNU make")
        # clean prior to make
        print("clean {} with makefile".format(target))
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
            print("build {} with makefile".format(target))
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
    ), "could not build {} with makefile".format(target)

    return


def test_clean_up():
    shutil.rmtree(cpth)


if __name__ == "__main__":
    test_gnu_make()
    test_clean_up()
