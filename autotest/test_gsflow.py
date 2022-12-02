import os
import shutil
import sys

import flopy
import pytest

import pymake

# use the line below to set fortran compiler using environmental variables
# os.environ["FC"] = "ifort"
# if sys.platform.lower() == "win32":
#     os.environ["CC"] = "icl"
# else:
#     os.environ["CC"] = "icc"


# define program data
target = "gsflow"
if sys.platform.lower() == "win32":
    target += ".exe"

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join(f"temp_{os.path.basename(__file__).replace('.py', '')}")
if not os.path.exists(dstpth):
    os.makedirs(dstpth, exist_ok=True)

gsflowver = prog_dict.version
gsflowpth = os.path.join(dstpth, prog_dict.dirname)
egsflow = os.path.abspath(os.path.join(dstpth, target))

# example path
expth = os.path.join(gsflowpth, "data")
examples = (("sagehen", "gsflow.control"),)

# set up pths and exes
pths = [gsflowpth]
exes = [egsflow]

pm = pymake.Pymake(verbose=True)
pm.target = target
pm.appdir = dstpth
pm.makeclean = True


def copy_example_dir(epth):
    if os.path.exists(egsflow):
        src = os.path.join(expth, epth)
        dst = os.path.join(dstpth, epth)

        # delete dst if it exists
        if os.path.isdir(dst):
            shutil.rmtree(dst)

        # copy the files
        try:
            shutil.copytree(src, dst)
        except:
            msg = f"could not move files from {src} to '{dst}'"
            raise NameError(msg)

        # edit the control file for a shorter run
        # sagehen
        example, control_file = examples[0]
        if epth == example:
            fpth = os.path.join(dstpth, epth, "linux", control_file)
            with open(fpth) as f:
                lines = f.readlines()
            with open(fpth, "w") as f:
                idx = 0
                while idx < len(lines):
                    line = lines[idx]
                    if "end_time" in line:
                        line += "6\n1\n1981\n"
                        idx += 3
                    f.write(line)
                    idx += 1
    return


def run_gsflow(example, control_file):
    success = False
    if os.path.exists(egsflow):
        # copy files
        copy_example_dir(example)

        model_ws = os.path.join(dstpth, example, "linux")

        # run the flow model
        success, buff = flopy.run_model(
            egsflow, control_file, model_ws=model_ws, silent=False
        )
        if not success:
            errmsg = f"could not run {control_file}"
    return success


def clean_up():
    print("Removing test files and directories")

    # finalize pymake object
    pm.finalize()

    # clean up downloaded directories
    if os.path.isdir(gsflowpth):
        print("Removing folder " + gsflowpth)
        shutil.rmtree(gsflowpth)

    # clean up examples
    for example, control_file in examples:
        pth = os.path.join(dstpth, example)
        if os.path.isdir(pth):
            print("Removing example folder " + example)
            shutil.rmtree(pth)

    # clean up compiled executables
    if os.path.isfile(egsflow):
        print("Removing...'" + egsflow + "'")
        os.remove(egsflow)

    dirs_temp = [dstpth]
    for d in dirs_temp:
        if os.path.isdir(d):
            shutil.rmtree(d)

    return


@pytest.mark.base
@pytest.mark.regression
def test_download():
    # Remove the existing target download directory if it exists
    if os.path.isdir(gsflowpth):
        shutil.rmtree(gsflowpth)

    # download the target
    pm.download_target(target, download_path=dstpth)
    assert pm.download, f"could not download {target} distribution"


@pytest.mark.base
@pytest.mark.regression
def test_compile():
    assert pm.build() == 0, f"could not compile {target}"


@pytest.mark.regression
@pytest.mark.parametrize("ex,cf", examples)
def test_gsflow(ex, cf):
    assert run_gsflow(ex, cf), f"could not run {ex}-{cf}"


@pytest.mark.base
@pytest.mark.regression
def test_clean_up():
    clean_up()
    return


if __name__ == "__main__":
    test_download()
    test_compile()
    for ex, cf in examples:
        assert run_gsflow(ex, cf), f"could not run {ex}-{cf}"
    test_clean_up()
