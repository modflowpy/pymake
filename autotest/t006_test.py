import os
import sys
import time
import shutil
import pymake

import pytest

# define program data
target = "mfnwt"
if sys.platform.lower() == "win32":
    target += ".exe"

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join("temp")
if not os.path.exists(dstpth):
    os.makedirs(dstpth)

mfnwtpth = os.path.join(dstpth, prog_dict.dirname)

srcpth = os.path.join(mfnwtpth, prog_dict.srcdir)
epth = os.path.join(dstpth, target)

pm = pymake.Pymake(verbose=True)
pm.target = target
pm.appdir = dstpth
pm.makefile = True
pm.inplace = True


def build_with_makefile():
    success = True
    if os.path.isfile("makefile"):
        # wait to delete on windows
        if sys.platform.lower() == "win32":
            time.sleep(6)

        print("Removing temporary build directories")
        dirs_temp = [
            os.path.join("src_temp"),
            os.path.join("obj_temp"),
            os.path.join("mod_temp"),
        ]
        for d in dirs_temp:
            if os.path.isdir(d):
                shutil.rmtree(d)

        # clean prior to make
        print("clean {} with makefile".format(target))
        os.system("make clean")

        # build MODFLOW-NWT with makefile
        print("build {} with makefile".format(target))
        return_code = os.system("make")

        # test if running on Windows with ifort, if True the makefile
        # should fail
        errmsg = "{} created by makefile does not exist.".format(target)
        if sys.platform.lower() == "win32" and pm.fc == "ifort":
            if return_code != 0:
                success = True
            else:
                success = False
        # verify that MODFLOW-NWT was made
        else:
            success = os.path.isfile(epth)
    else:
        errmsg = "makefile does not exist"

    assert success, errmsg

    return


def clean_up():
    # clean up make file
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

    # finalize pymake object
    pm.finalize()

    # clean up MODFLOW-NWT
    if os.path.isfile(epth):
        print("Removing " + target)
        os.remove(epth)

    return


@pytest.mark.base
@pytest.mark.regression
def test_download():
    # Remove the existing mf2005 directory if it exists
    if os.path.isdir(mfnwtpth):
        shutil.rmtree(mfnwtpth)

    # download the modflow 2005 release
    pm.download_target(target, download_path=dstpth)
    assert pm.download, "could not download {} distribution".format(target)


@pytest.mark.base
@pytest.mark.regression
def test_compile():
    assert pm.build() == 0, "could not compile {}".format(target)


@pytest.mark.base
@pytest.mark.regression
def test_makefile():
    build_with_makefile()


@pytest.mark.base
@pytest.mark.regression
def test_clean_up():
    clean_up()


if __name__ == "__main__":
    test_download()
    test_compile()
    build_with_makefile()
    clean_up()
