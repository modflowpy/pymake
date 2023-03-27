import os
import shutil
import sys

import flopy
import pytest

import pymake

# use the line below to set fortran compiler using environmental variables
# os.environ["FC"] = "ifort"
# os.environ["CC"] = "icc"


# define program data
target = "mf2005"
if sys.platform.lower() == "win32":
    target += ".exe"

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join(f"temp_{os.path.basename(__file__).replace('.py', '')}")
if not os.path.exists(dstpth):
    os.makedirs(dstpth, exist_ok=True)

mfver = prog_dict.version
mfpth = os.path.join(dstpth, prog_dict.dirname)
expth = os.path.join(mfpth, "test-run")
epth = os.path.join(dstpth, target)
name_files = [
    "l1b2k_bath.nam",
    "test1tr.nam",
    "mnw1.nam",
    "testsfr2.nam",
    "bcf2ss.nam",
    "restest.nam",
    "etsdrt.nam",
    "str.nam",
    "tr2k_s3.nam",
    "fhb.nam",
    "twri.nam",
    "ibs2k.nam",
    "swtex4.nam",
    "twrihfb.nam",
    "l1a2k.nam",
    "tc2hufv4.nam",
    "twrip.nam",
    "l1b2k.nam",
    "test1ss.nam",
]
# add path to name_files
for idx, namefile in enumerate(name_files):
    name_files[idx] = os.path.join(expth, namefile)

pm = pymake.Pymake(verbose=True)
pm.target = target
pm.appdir = dstpth
pm.fflags = "-O3"
pm.cflags = "-O3"


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

        # run test models
        exe_name = os.path.abspath(epth)
        msg = f"running model...{testname}" + f" using {exe_name}"
        print(msg)
        if os.path.exists(exe_name):
            success, buff = flopy.run_model(
                exe_name, nam, model_ws=testpth, silent=True
            )
        else:
            success = False

        assert success, f"base model {nam} " + "did not run."

        # Clean things up
        if success:
            if os.path.exists(testpth):
                print("Removing folder " + testpth)
                shutil.rmtree(testpth)
        else:
            success = False
            errmsg = f"could not run...{os.path.basename(nam)}"
    else:
        success = False
        errmsg = f"{target} does not exist"

    assert success, errmsg

    return


def cleanup():
    print("Removing test files and directories")

    # clean up makefile
    print("Removing makefile")
    files = ["makefile", "makedefaults"]
    for fpth in files:
        if os.path.isfile(fpth):
            os.remove(fpth)

    # finalize pymake object
    pm.finalize()

    if os.path.isfile(epth):
        print("Removing " + target)
        os.remove(epth)

    dirs_temp = [dstpth]
    for d in dirs_temp:
        if os.path.isdir(d):
            shutil.rmtree(d)

    return


@pytest.mark.base
def test_download():
    # Remove the existing target download directory if it exists
    if os.path.isdir(mfpth):
        shutil.rmtree(mfpth)

    # download the target
    pm.download_target(target, download_path=dstpth)
    assert pm.download, f"could not download {target}"


@pytest.mark.base
def test_compile():
    assert pm.build() == 0, f"could not compile {target}"


@pytest.mark.regression
@pytest.mark.skipif(sys.platform == "darwin", reason="do not run on OSX")
@pytest.mark.parametrize("fn", name_files)
def test_mf2005(fn):
    run_mf2005(fn)
    return


@pytest.mark.base
def test_cleanup():
    cleanup()

    return


if __name__ == "__main__":
    test_download()

    test_compile()

    for namefile in name_files:
        run_mf2005(namefile)

    test_cleanup()
