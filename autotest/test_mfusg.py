import os
import shutil
import sys

import flopy
import pytest

import pymake

# define program data
target = "mfusg"
target_gsi = "mfusg_gsi"
if sys.platform.lower() == "win32":
    target += ".exe"
    target_gsi += ".exe"

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join(f"temp_{os.path.basename(__file__).replace('.py', '')}")
if not os.path.exists(dstpth):
    os.makedirs(dstpth, exist_ok=True)

mfusgpth = os.path.join(dstpth, prog_dict.dirname)
expth = os.path.join(mfusgpth, "test")

srcpth = os.path.join(mfusgpth, prog_dict.srcdir)
epth = os.path.abspath(os.path.join(dstpth, target))
epth_gsi = os.path.abspath(os.path.join(dstpth, target_gsi))

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

run_parameters = []
for ep in (epth, epth_gsi):
    for nf in name_files:
        run_parameters.append((ep, nf))

pm = pymake.Pymake(verbose=True)
pm.target = target
pm.appdir = dstpth

pm_gsi = pymake.Pymake(verbose=True)
pm_gsi.target = target_gsi
pm_gsi.appdir = dstpth

usg_versions = (
    (0, pm),
    (1, pm_gsi),
)


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

    # finalize pymake objects
    pm.finalize()
    pm_gsi.finalize()

    if os.path.isfile(epth):
        print("Removing " + target)
        os.remove(epth)

    if os.path.isfile(epth_gsi):
        print("Removing " + target_gsi)
        os.remove(epth_gsi)

    dirs_temp = [dstpth]
    for d in dirs_temp:
        if os.path.isdir(d):
            shutil.rmtree(d)

    return


def run_mfusg(fn, exe):
    # edit namefile
    edit_namefile(fn)
    # run test models
    print(f"running model...{os.path.basename(fn)}")
    success, buff = flopy.run_model(
        exe, os.path.basename(fn), model_ws=os.path.dirname(fn), silent=False
    )
    errmsg = f"could not run {fn} with {exe}"
    assert success, errmsg

    return


@pytest.mark.base
@pytest.mark.parametrize("idx,pmobj", usg_versions)
def test_download(idx, pmobj):
    # Remove the existing mfusg directory if it exists
    if idx == 0:
        if os.path.isdir(mfusgpth):
            shutil.rmtree(mfusgpth)

    # download the modflow-usg release
    pmobj.download_target(pmobj.target, download_path=dstpth)
    assert pmobj.download, f"could not download {pmobj.target}"


@pytest.mark.base
@pytest.mark.parametrize("idx,pmobj", usg_versions)
def test_compile(idx, pmobj):
    assert pmobj.build() == 0, f"could not compile {pmobj.target}"
    return


@pytest.mark.regression
@pytest.mark.parametrize("usg_path,fn", run_parameters)
def test_mfusg(usg_path, fn):
    run_mfusg(fn, usg_path)


@pytest.mark.base
def test_clean_up():
    clean_up()


if __name__ == "__main__":
    for idx, pmobj in usg_versions:
        test_download(idx, pmobj)
        test_compile(idx, pmobj)

    # run models
    for usg_exe, namefile in run_parameters:
        run_mfusg(usg_exe, namefile)

    # clean up
    test_clean_up()
