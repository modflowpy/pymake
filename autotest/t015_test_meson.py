import os
import shutil
import sys

import flopy
import pytest

import pymake

# define program data
target = "prms"

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join(f"temp_{os.path.basename(__file__).replace('.py', '')}")
if not os.path.exists(dstpth):
    os.makedirs(dstpth, exist_ok=True)

prmsver = prog_dict.version
prmspth = os.path.join(dstpth, prog_dict.dirname)

# example path
expth = os.path.join(prmspth, "projects")
examples = (
    (
        "sagehen",
        os.path.join("control", "sagehen.control"),
    ),
    (
        "acf",
        os.path.join("control", "acf.control"),
    ),
)

pm = pymake.Pymake(verbose=True)
pm.target = target
pm.appdir = os.path.join(dstpth, "bin")
pm.meson = True
pm.mesondir = os.path.join(dstpth)

if sys.platform.lower() == "win32":
    target += ".exe"
eprms = os.path.abspath(os.path.join(pm.appdir, target))

# set up pths and exes
pths = [prmspth]
exes = [eprms]


def copy_example_dir(epth):
    if os.path.exists(eprms):
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

        # # edit the control file for a shorter run
        # # sagehen
        # example, control_file = examples[0]
        # if epth == example:
        #     fpth = os.path.join(dstpth, epth, "linux", control_file)
        #     with open(fpth) as f:
        #         lines = f.readlines()
        #     with open(fpth, "w") as f:
        #         idx = 0
        #         while idx < len(lines):
        #             line = lines[idx]
        #             if "end_time" in line:
        #                 line += "6\n1\n1981\n"
        #                 idx += 3
        #             f.write(line)
        #             idx += 1
    return


def run_prms(example, control_file):
    success = False
    if os.path.exists(eprms):
        # copy files
        copy_example_dir(example)

        model_ws = os.path.join(dstpth, example)

        # run the flow model
        success, buff = flopy.run_model(
            eprms,
            control_file,
            model_ws=model_ws,
            silent=False,
            normal_msg="Normal completion of PRMS",
        )
        if not success:
            errmsg = f"could not run {control_file}"
    return success


def clean_up():
    print("Removing test files and directories")

    # finalize pymake object
    pm.finalize()

    # clean up downloaded directories
    if os.path.isdir(prmspth):
        print("Removing folder " + prmspth)
        shutil.rmtree(prmspth)

    # clean up examples
    for example, control_file in examples:
        pth = os.path.join(dstpth, example)
        if os.path.isdir(pth):
            print("Removing example folder " + example)
            shutil.rmtree(pth)

    # clean up compiled executables
    if os.path.isfile(eprms):
        print("Removing...'" + eprms + "'")
        os.remove(eprms)

    dirs_temp = [dstpth]
    for d in dirs_temp:
        if os.path.isdir(d):
            shutil.rmtree(d)

    return


@pytest.mark.base
@pytest.mark.regression
def test_download():
    # Remove the existing target download directory if it exists
    if os.path.isdir(prmspth):
        shutil.rmtree(prmspth)

    # download the target
    pm.download_target(target, download_path=dstpth)
    assert pm.download, f"could not download {target} distribution"


@pytest.mark.base
@pytest.mark.regression
def test_compile():
    assert pm.build() == 0, f"could not compile {target}"


@pytest.mark.regression
@pytest.mark.parametrize("ex,cf", examples)
def test_prms(ex, cf):
    assert run_prms(ex, cf), f"could not run {ex}-{cf}"


@pytest.mark.base
@pytest.mark.regression
def test_clean_up():
    clean_up()
    return


if __name__ == "__main__":
    test_download()
    test_compile()
    for ex, cf in examples:
        assert run_prms(ex, cf), f"could not run {ex}-{cf}"
    test_clean_up()
