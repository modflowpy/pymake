import os
import sys
import shutil

import pymake
import flopy

import pytest

# define program data
target = "swtv4"
if sys.platform.lower() == "win32":
    target += ".exe"

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join("temp")
if not os.path.exists(dstpth):
    os.makedirs(dstpth)

swtpth = os.path.join(dstpth, prog_dict.dirname)
expth = os.path.join(swtpth, "examples")
deppth = os.path.join(swtpth, "dependencies")

srcpth = os.path.join(swtpth, prog_dict.srcdir)
epth = os.path.abspath(os.path.join(dstpth, target))

name_files = sorted(
    [
        "4_hydrocoin/seawat.nam",
        "5_saltlake/seawat.nam",
        "2_henry/1_classic_case1/seawat.nam",
        "2_henry/4_VDF_uncpl_Trans/seawat.nam",
        "2_henry/5_VDF_DualD_Trans/seawat.nam",
        "2_henry/6_age_simulation/henry_mod.nam",
        "2_henry/2_classic_case2/seawat.nam",
        "2_henry/3_VDF_no_Trans/seawat.nam",
        "1_box/case1/seawat.nam",
        "1_box/case2/seawat.nam",
        "3_elder/seawat.nam",
    ]
)
# add path to name_files
for idx, namefile in enumerate(name_files):
    name_files[idx] = os.path.join(expth, namefile)

pm = pymake.Pymake(verbose=True)
pm.target = target
pm.appdir = dstpth
pm.double = True


def edit_namefile(namefile):
    # read existing namefile
    f = open(namefile, "r")
    lines = f.read().splitlines()
    f.close()
    # remove global line
    f = open(namefile, "w")
    for line in lines:
        if "global" in line.lower():
            continue
        f.write("{}\n".format(line))
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


def run_seawat(fn):
    # edit the name files
    edit_namefile(fn)

    # run the models
    success, buff = flopy.run_model(
        epth, os.path.basename(fn), model_ws=os.path.dirname(fn), silent=False
    )
    errmsg = "could not run...{}".format(os.path.basename(fn))
    assert success, errmsg
    return


def build_seawat_dependency_graphs():
    if os.path.exists(epth):

        # build dependencies output directory
        if not os.path.exists(deppth):
            os.makedirs(deppth)

        # build dependency graphs
        print("building dependency graphs")
        pymake.make_plots(srcpth, deppth, verbose=True)

        # test that the dependency figure for the SEAWAT main exists
        findf = os.path.join(deppth, "swt_v4.f.png")
        success = os.path.isfile(findf)
        assert success, "could not find {}".format(findf)
    else:
        success = False

    assert success, "could not build dependency graphs"

    return


def test_download():
    # Remove the existing seawat directory if it exists
    if os.path.isdir(swtpth):
        shutil.rmtree(swtpth)

    # download the target
    pm.download_target(target, download_path=dstpth)
    assert pm.download, "could not download {}".format(target)


def test_compile():
    assert pm.build() == 0, "could not compile {}".format(target)


@pytest.mark.parametrize("fn", name_files)
def test_seawat(fn):
    run_seawat(fn)


def test_dependency_graphs():
    build_seawat_dependency_graphs()


def test_clean_up():
    clean_up()


if __name__ == "__main__":
    test_download()
    test_compile()
    for fn in name_files:
        run_seawat(fn)
    test_dependency_graphs()
    test_clean_up()
