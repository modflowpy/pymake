import os
import shutil
import sys

import flopy
import pytest

import pymake

# define program data
target = "mp6"
if sys.platform.lower() == "win32":
    target += ".exe"

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join(f"temp_{os.path.basename(__file__).replace('.py', '')}")
if not os.path.exists(dstpth):
    os.makedirs(dstpth, exist_ok=True)

mp6pth = os.path.join(dstpth, prog_dict.dirname)
expth = os.path.join(mp6pth, "example-run")

sim_files = [f"EXAMPLE-{n}.mpsim" for n in range(1, 10)]

exe_name = target
srcpth = os.path.join(mp6pth, prog_dict.srcdir)
epth = os.path.abspath(os.path.join(dstpth, target))

pm = pymake.Pymake(verbose=True)
pm.target = target
pm.appdir = dstpth


def update_files(fn):
    # rename a few files for linux
    replace_files = ["example-6", "example-7", "example-8"]
    for rf in replace_files:
        if rf in fn.lower():
            fname1 = os.path.join(expth, f"{rf}.locations")
            fname2 = os.path.join(expth, f"{rf}_mod.locations")
            print(
                "copy {} to {}".format(
                    os.path.basename(fname1), os.path.basename(fname2)
                )
            )
            shutil.copy(fname1, fname2)
            print(f"deleting {os.path.basename(fname1)}")
            os.remove(fname1)
            fname1 = os.path.join(expth, f"{rf.upper()}.locations")
            print(
                "renmae {} to {}".format(
                    os.path.basename(fname2), os.path.basename(fname1)
                )
            )
            os.rename(fname2, fname1)


def run_modpath6(fn):
    success = False
    if os.path.exists(epth):
        update_files(fn)
        # run the model
        print(f"running model...{fn}")
        success, buff = flopy.run_model(epth, fn, model_ws=expth, silent=False)
    return success


def clean_up():
    print("Removing test files and directories")

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
    if os.path.isdir(mp6pth):
        shutil.rmtree(mp6pth)

    pm.download_target(target, download_path=dstpth)
    assert pm.download, f"could not download {target} distribution"


@pytest.mark.base
def test_compile():
    assert pm.build() == 0, f"could not compile {target}"


@pytest.mark.regression
@pytest.mark.parametrize("fn", sim_files)
def test_modpath6(fn):
    assert run_modpath6(fn), f"could not run {fn}"


@pytest.mark.base
def test_clean_up():
    clean_up()


if __name__ == "__main__":
    test_download()
    test_compile()
    for fn in sim_files:
        run_modpath6(fn)
    test_clean_up()
