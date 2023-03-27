import os
import shutil
import sys

import flopy
import pytest

import pymake

# determine if running on a continuous integration server
is_CI = "CI" in os.environ

# define program data
target = "swtv4"
if sys.platform.lower() == "win32":
    target += ".exe"

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join(f"temp_{os.path.basename(__file__).replace('.py', '')}")
if not os.path.exists(dstpth):
    os.makedirs(dstpth, exist_ok=True)

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
        f.write(f"{line}\n")
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


def run_seawat(fn):
    # edit the name files
    edit_namefile(fn)

    # run the models
    success, buff = flopy.run_model(
        epth, os.path.basename(fn), model_ws=os.path.dirname(fn), silent=False
    )
    errmsg = f"could not run...{os.path.basename(fn)}"
    assert success, errmsg
    return


def build_seawat_dependency_graphs():
    success = True
    build_graphs = True
    if is_CI:
        if "linux" not in sys.platform.lower():
            build_graphs = False

    if build_graphs:
        if os.path.exists(epth):
            # build dependencies output directory
            if not os.path.exists(deppth):
                os.makedirs(deppth, exist_ok=True)

            # build dependency graphs
            print("building dependency graphs")
            pymake.make_plots(srcpth, deppth, verbose=True)

            # test that the dependency figure for the SEAWAT main exists
            findf = os.path.join(deppth, "swt_v4.f.png")
            success = os.path.isfile(findf)
            assert success, f"could not find {findf}"

    assert success, "could not build dependency graphs"

    return


@pytest.mark.base
def test_download():
    # Remove the existing seawat directory if it exists
    if os.path.isdir(swtpth):
        shutil.rmtree(swtpth)

    # download the target
    pm.download_target(target, download_path=dstpth)
    assert pm.download, f"could not download {target}"


@pytest.mark.base
def test_compile():
    assert pm.build() == 0, f"could not compile {target}"


@pytest.mark.regression
@pytest.mark.parametrize("fn", name_files)
def test_seawat(fn):
    run_seawat(fn)


@pytest.mark.regression
def test_dependency_graphs():
    build_seawat_dependency_graphs()


@pytest.mark.base
@pytest.mark.regression
def test_clean_up():
    clean_up()


if __name__ == "__main__":
    test_download()
    test_compile()
    for fn in name_files:
        run_seawat(fn)
    test_dependency_graphs()
    test_clean_up()
