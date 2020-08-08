import os
import sys
import shutil
import pymake
import flopy

# working directory
cpth = os.path.abspath(os.path.join("temp", "t013"))
if os.path.isdir(cpth):
    shutil.rmtree(cpth)
os.makedirs(cpth)


def test_gnu_make():
    target = "triangle"
    pm = pymake.Pymake(verbose=True)

    # add test arguments from command line list
    cargs = ("--makefile", "-mc")
    for arg in cargs:
        sys.argv.append(arg)

    # get current directory
    cwd = os.getcwd()

    # change to working directory so triangle download directory is
    # a subdirectory in the working directory
    os.chdir(cpth)

    # build triangle and makefile
    assert (
        pymake.build_apps(target, clean=False, pymake_object=pm) == 0
    ), "could not build {}".format(target)

    # remove test arguments from command line list
    for arg in cargs:
        sys.argv.remove(arg)

    if os.path.isfile(os.path.join(cpth, "makefile")):
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
    # test_clean_up()
