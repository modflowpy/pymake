import os
import sys
import shutil

import pytest

import pymake
import flopy

# define program data
target = "mp6"
if sys.platform.lower() == "win32":
    target += ".exe"

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join("temp")
if not os.path.exists(dstpth):
    os.makedirs(dstpth)

mp6pth = os.path.join(dstpth, prog_dict.dirname)
expth = os.path.join(mp6pth, "example-run")

sim_files = ["EXAMPLE-{}.mpsim".format(n) for n in range(1, 10)]

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
            fname1 = os.path.join(expth, "{}.locations".format(rf))
            fname2 = os.path.join(expth, "{}_mod.locations".format(rf))
            print(
                "copy {} to {}".format(
                    os.path.basename(fname1), os.path.basename(fname2)
                )
            )
            shutil.copy(fname1, fname2)
            print("deleting {}".format(os.path.basename(fname1)))
            os.remove(fname1)
            fname1 = os.path.join(expth, "{}.locations".format(rf.upper()))
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
        print("running model...{}".format(fn))
        success, buff = flopy.run_model(epth, fn, model_ws=expth, silent=False)
    return success


def clean_up():
    print("Removing temporary build directories")
    dirs_temp = [os.path.join("obj_temp"), os.path.join("mod_temp")]
    for d in dirs_temp:
        if os.path.isdir(d):
            shutil.rmtree(d)

    # finalize pymake object
    pm.finalize()

    if os.path.isfile(epth):
        print("Removing " + target)
        os.remove(epth)
    return


def test_download():
    if os.path.isdir(mp6pth):
        shutil.rmtree(mp6pth)

    pm.download_target(target, download_path=dstpth)
    assert pm.download, "could not download {} distribution".format(target)


def test_compile():
    assert pm.build() == 0, "could not compile {}".format(target)


@pytest.mark.all
@pytest.mark.parametrize("fn", sim_files)
def test_modpath6(fn):
    assert run_modpath6(fn), "could not run {}".format(fn)


def test_clean_up():
    clean_up()


if __name__ == "__main__":
    test_download()
    test_compile()
    for fn in sim_files:
        run_modpath6(fn)
    test_clean_up()
