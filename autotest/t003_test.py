import os
import shutil
import sys

import flopy
import pytest

import pymake

# define program data
target = "mfusg"
if sys.platform.lower() == "win32":
    target += ".exe"

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join(f"temp_{os.path.basename(__file__).replace('.py', '')}")
if not os.path.exists(dstpth):
    os.makedirs(dstpth)

mfusgpth = os.path.join(dstpth, prog_dict.dirname)
expth = os.path.join(mfusgpth, "test")

srcpth = os.path.join(mfusgpth, prog_dict.srcdir)
epth = os.path.abspath(os.path.join(dstpth, target))

name_files = [
    "01A_nestedgrid_nognc/flow.nam",
    "01B_nestedgrid_gnc/flow.nam",
    "03A_conduit_unconfined/ex3A.nam",
    "03B_conduit_unconfined/ex3B.nam",
    "03C_conduit_unconfined/ex3C.nam",
    "03D_conduit_unconfined/ex3D.nam",
    "03_conduit_confined/ex3.nam",
]
# add path to name_files
for idx, namefile in enumerate(name_files):
    name_files[idx] = os.path.join(expth, namefile)

pm = pymake.Pymake(verbose=True)
pm.target = target
pm.appdir = dstpth


def edit_namefile(namefile):
    # read existing namefile
    f = open(namefile, "r")
    lines = f.read().splitlines()
    f.close()
    # convert file extensions to lower case
    f = open(namefile, "w")
    for line in lines:
        t = line.split()
        fn, ext = os.path.splitext(t[2])
        f.write(f"{t[0]:15s} {t[1]:3s} {fn}{ext.lower()} ")
        if len(t) > 3:
            f.write(f"{t[3]}")
        f.write("\n")
    f.close()


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


def run_mfusg(fn):
    # edit namefile
    edit_namefile(fn)
    # run test models
    print(f"running model...{os.path.basename(fn)}")
    success, buff = flopy.run_model(
        epth, os.path.basename(fn), model_ws=os.path.dirname(fn), silent=False
    )
    errmsg = f"could not run {fn}"
    assert success, errmsg

    return


@pytest.mark.base
@pytest.mark.regression
def test_download():
    # Remove the existing mf2005 directory if it exists
    if os.path.isdir(mfusgpth):
        shutil.rmtree(mfusgpth)

    # download the modflow-usg release
    pm.download_target(target, download_path=dstpth)
    assert pm.download, f"could not download {target}"


@pytest.mark.base
@pytest.mark.regression
def test_compile():
    assert pm.build() == 0, f"could not compile {target}"
    return


@pytest.mark.regression
@pytest.mark.parametrize("fn", name_files)
def test_mfusg(fn):
    run_mfusg(fn)


@pytest.mark.base
@pytest.mark.regression
def test_clean_up():
    clean_up()


if __name__ == "__main__":
    test_download()

    test_compile()

    # run models
    for namefile in name_files:
        run_mfusg(namefile)

    # clean up
    test_clean_up()
