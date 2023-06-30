import os
import pathlib as pl
import shutil
import sys

import flopy
import pytest
from flaky import flaky

import pymake

RERUNS = 3

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
examples = (
    ("sagehen", "prms.control", "Normal completion"),
    ("sagehen", "gsflow.control", "Normal termination of simulation"),
    ("sagehen", "modflow.control", "Normal termination of simulation"),
)

# set up pths and exes
pths = [gsflowpth]
exes = [egsflow]

pm = pymake.Pymake(verbose=True)
pm.target = target
pm.appdir = dstpth
pm.makeclean = True


def copy_example_dir():
    if os.path.exists(egsflow):
        src = os.path.join(expth, "sagehen")
        dst = os.path.join(dstpth, "sagehen")

        # delete dst if it exists
        if os.path.isdir(dst):
            shutil.rmtree(dst)

        # copy the files
        try:
            shutil.copytree(src, dst)
        except:
            print(f"could not move files from {src} to '{dst}'")
            return False

        # edit the control file for a shorter run
        # sagehen
        tags = {
            "..\\input\\prms\\": "../input/prms/",
            ".\\input\\modflow\\": "./input/modflow/",
            "..\\output\\": "../output/",
            "..\\output\\prms\\": "../output/prms/",
            "..\\output\\modflow\\": "../output/modflow/",
        }

        for _, control_file, _ in examples[1:]:
            fpth = pl.Path(f"{dst}/windows/{control_file}")
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

        # modify available control and name files
        base_paths = (
            pl.Path(f"{dst}/windows"),
            pl.Path(f"{dst}/input/modflow"),
        )
        file_paths = []
        for base_path in base_paths:
            file_paths += base_path.glob("*.control")
            file_paths += base_path.glob("*.nam")
        for file_path in file_paths:
            with open(file_path) as f:
                lines = f.readlines()
            with open(file_path, "w") as f:
                for line in lines:
                    for key, value in tags.items():
                        if key in line:
                            line = line.replace(key, value)
                    f.write(line)

    return True


def run_gsflow(example, control_file, normal_message):
    success = False
    if os.path.exists(egsflow):
        model_ws = os.path.join(dstpth, example, "windows")

        # run the flow model
        success, buff = flopy.run_model(
            egsflow,
            control_file,
            model_ws=model_ws,
            silent=False,
            normal_msg=normal_message,
        )
        if not success:
            print(f"could not run {control_file}")
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
    for example, _, _ in examples:
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
@flaky(max_runs=RERUNS)
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
def test_prepare_regression():
    assert copy_example_dir(), "could not prepare regression files"


@pytest.mark.regression
@pytest.mark.parametrize("ex,cf,msg", examples)
def test_gsflow(ex, cf, msg):
    assert run_gsflow(ex, cf, msg), f"could not run {ex}-{cf}"


@pytest.mark.base
@pytest.mark.regression
def test_clean_up():
    clean_up()
    return


if __name__ == "__main__":
    test_download()
    test_compile()
    test_prepare_regression()
    for ex, cf, msg in examples:
        assert run_gsflow(ex, cf, msg), f"could not run {ex}-{cf}"
    test_clean_up()
