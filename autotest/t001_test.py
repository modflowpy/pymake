import os
import sys
import shutil

import pymake
from pymake.autotest import get_namefiles

import flopy

# define program data
target = "mf2005"
if sys.platform.lower() == "win32":
    target += ".exe"

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join("temp")
if not os.path.exists(dstpth):
    os.makedirs(dstpth)

mfver = prog_dict.version
mfpth = os.path.join(dstpth, prog_dict.dirname)
expth = os.path.join(mfpth, "test-run")
epth = os.path.join(dstpth, target)
exclude = ("MNW2-Fig28", "swi2ex4sww", "testsfr2_tab", "UZFtest2")

pm = pymake.Pymake(verbose=True)
pm.target = target
pm.appdir = dstpth
pm.fflags = "-O3 -fbacktrace"
pm.cflags = "-O3"


def download_src():
    # Remove the existing target download directory if it exists
    if os.path.isdir(mfpth):
        shutil.rmtree(mfpth)

    # download the target
    pm.download_target(target, download_path=dstpth)


def mf2005_namefiles():
    if os.path.isdir(expth):
        namefiles = get_namefiles(expth, exclude=exclude)
    else:
        namefiles = [None]
    return namefiles


def run_mf2005(namefile, regression=True):
    """
    Run the simulation.

    """
    if namefile is not None:
        # Set root as the directory name where namefile is located
        testname = pymake.get_sim_name(namefile, rootpth=expth)[0]

        # Set nam as namefile name without path
        nam = os.path.basename(namefile)

        # Setup
        testpth = os.path.join(dstpth, testname)
        pymake.setup(namefile, testpth)

        # run test models
        exe_name = os.path.abspath(epth)
        msg = "running model...{}".format(testname) + " using {}".format(
            exe_name
        )
        print(msg)
        if os.path.exists(exe_name):
            success, buff = flopy.run_model(
                exe_name, nam, model_ws=testpth, silent=True
            )
        else:
            success = False

        assert success, "base model {} ".format(nam) + "did not run."

        # If it is a regression run, then setup and run the model with the
        # release target and the reference target
        success_reg = True
        if regression:
            testname_reg = os.path.basename(mfpth)
            testpth_reg = os.path.join(testpth, testname_reg)
            pymake.setup(namefile, testpth_reg)
            # exe_name = os.path.abspath(target_previous)
            msg = "running regression model...{}".format(
                testname_reg
            ) + " using {}".format(exe_name)
            print(msg)

            if os.path.exists(exe_name):
                success_reg, buff = flopy.run_model(
                    exe_name, nam, model_ws=testpth_reg, silent=False
                )
            else:
                success_reg = False

            assert success_reg, (
                "regression model {} ".format(nam) + "did not run."
            )

        # compare results
        if success and success_reg:
            fpth = os.path.split(os.path.join(testpth, nam))[0]
            outfile1 = os.path.join(fpth, "bud.cmp")
            fpth = os.path.split(os.path.join(testpth, nam))[0]
            outfile2 = os.path.join(fpth, "hds.cmp")
            success_reg = pymake.compare(
                os.path.join(testpth, nam),
                os.path.join(testpth_reg, nam),
                precision="single",
                max_cumpd=0.01,
                max_incpd=0.01,
                htol=0.001,
                outfile1=outfile1,
                outfile2=outfile2,
            )
        # Clean things up
        if success_reg:
            pymake.teardown(testpth)
        else:
            success = False
            errmsg = "could not run...{}".format(os.path.basename(nam))
    else:
        success = False
        errmsg = "{} does not exist".format(target)

    assert success, errmsg

    return


def cleanup():
    # clean up makefile
    print("Removing makefile")
    files = ["makefile", "makedefaults"]
    for fpth in files:
        if os.path.isfile(fpth):
            os.remove(fpth)

    print("Removing temporary build directories")
    dirs_temp = [os.path.join("obj_temp"), os.path.join("mod_temp")]
    for d in dirs_temp:
        if os.path.isdir(d):
            shutil.rmtree(d)

    # remove download directory
    pm.download_cleanup()

    if os.path.isfile(epth):
        print("Removing " + target)
        os.remove(epth)
    return


def test_download():
    download_src()


def test_compile():
    pm.build()


def test_mf2005():
    for namefile in mf2005_namefiles():
        yield run_mf2005, namefile
    return


def test_cleanup():
    cleanup()

    return


if __name__ == "__main__":
    test_download()

    test_compile()

    for namefile in mf2005_namefiles():
        run_mf2005(namefile)

    test_cleanup()
