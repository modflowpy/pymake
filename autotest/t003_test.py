import os
import sys
import shutil
import pymake
import flopy

import pytest

# define program data
target = "mfusg"
if sys.platform.lower() == "win32":
    target += ".exe"

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join("temp")
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
        f.write(
            "{:15s} {:3s} {} ".format(
                t[0], t[1], "{}{}".format(fn, ext.lower())
            )
        )
        if len(t) > 3:
            f.write("{}".format(t[3]))
        f.write("\n")
    f.close()


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


def run_mfusg(fn):
    # edit namefile
    edit_namefile(fn)
    # run test models
    print("running model...{}".format(os.path.basename(fn)))
    success, buff = flopy.run_model(
        epth, os.path.basename(fn), model_ws=os.path.dirname(fn), silent=False
    )
    errmsg = "could not run {}".format(fn)
    assert success, errmsg

    return


def test_download():
    # Remove the existing mf2005 directory if it exists
    if os.path.isdir(mfusgpth):
        shutil.rmtree(mfusgpth)

    # download the modflow-usg release
    pm.download_target(target, download_path=dstpth)
    assert pm.download, "could not download {}".format(target)


def test_compile():
    assert pm.build() == 0, "could not compile {}".format(target)
    return


@pytest.mark.all
@pytest.mark.parametrize("fn", name_files)
def test_mfusg(fn):
    run_mfusg(fn)


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
