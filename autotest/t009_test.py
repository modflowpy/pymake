import os
import shutil
import sys

import flopy
import pytest

import pymake

# define program data
target = "mt3dusgs"

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join(f"temp_{os.path.basename(__file__).replace('.py', '')}")
if not os.path.exists(dstpth):
    os.makedirs(dstpth, exist_ok=True)

mtusgsver = prog_dict.version
mtusgspth = os.path.join(dstpth, prog_dict.dirname)
emtusgs = os.path.abspath(os.path.join(dstpth, target))

mfnwt_target = "mfnwt"
temp_dict = pymake.usgs_program_data().get_target(mfnwt_target)
emfnwt = os.path.abspath(os.path.join(dstpth, mfnwt_target))

mf6_target = "mf6"
temp_dict = pymake.usgs_program_data().get_target(mf6_target)
emf6 = os.path.abspath(os.path.join(dstpth, mf6_target))

if sys.platform.lower() == "win32":
    ext = ".exe"
    emtusgs += ext
    emfnwt += ext
    emf6 += ext

# example path
expth = os.path.join(mtusgspth, "data")

# set up pths and exes
epths = [emtusgs, emfnwt, emf6]

pm = pymake.Pymake(verbose=True)
pm.appdir = dstpth
pm.makeclean = True

sim_dirs = [
    "2ED5EAs",
    "CTS1",
    "CTS2",
    "CTS3",
    "CTS4",
    "Keating",
    "Keating_UZF",
    "SFT_CrnkNic",
    "UZT_Disp_Lamb01_TVD",
    "UZT_Disp_Lamb1",
    "UZT_Disp_Lamb10",
    "UZT_NonLin",
    "gwt",
    "lkt",
    "p01SpatialStresses(mf6)",
]

# remove after MODFLOW 6 v6.1.2 release
for exclude in (
    "Keating",
    "Keating_UZF",
):
    if exclude in sim_dirs:
        sim_dirs.remove(exclude)

# CI fix
if pymake.usgs_program_data().get_version(mfnwt_target) == "1.2.0":
    for exclude in (
        "UZT_NonLin",
        "UZT_Disp_Lamb01_TVD",
        "UZT_Disp_Lamb1",
        "UZT_Disp_Lamb10",
    ):
        if exclude in sim_dirs:
            sim_dirs.remove(exclude)


def run_mt3dusgs(temp_dir):
    success = False
    if os.path.exists(emtusgs):
        model_ws = os.path.join(expth, temp_dir)

        files = [
            f
            for f in os.listdir(model_ws)
            if os.path.isfile(os.path.join(model_ws, f))
        ]

        mf_nam = None
        mt_nam = None
        flow_model = None
        for f in files:
            if "_mf.nam" in f.lower():
                mf_nam = f
                flow_model = "mfnwt"
            if "_mt.nam" in f.lower():
                mt_nam = f
            if f == "mfsim.nam":
                mf_nam = f
                flow_model = "mf6"

        msg = f"A MODFLOW name file not present in {model_ws}"
        assert mf_nam is not None, msg

        msg = f"A MT3D-USGS name file not present in {model_ws}"
        assert mt_nam is not None, msg

        # run the flow model
        msg = f"{emfnwt}"
        if mf_nam is not None:
            msg += f" {os.path.basename(mf_nam)}"
        if flow_model == "mfnwt":
            nam = mf_nam
            eapp = emfnwt
        elif flow_model == "mf6":
            nam = None
            eapp = emf6
        success, buff = flopy.run_model(
            eapp, nam, model_ws=model_ws, silent=False
        )

        # run the MT3D-USGS model
        if success:
            print(f"running model...{mt_nam}")
            success, buff = flopy.run_model(
                emtusgs,
                mt_nam,
                model_ws=model_ws,
                silent=False,
                normal_msg="Program completed.",
            )

    return success


def clean_up():
    print("Removing test files and directories")

    # finalize pymake object
    pm.finalize()

    for epth in epths:
        if os.path.isfile(epth):
            print("Removing '" + epth + "'")
            os.remove(epth)

    dirs_temp = (dstpth,)
    for d in dirs_temp:
        if os.path.isdir(d):
            shutil.rmtree(d)

    return


@pytest.mark.base
@pytest.mark.regression
def test_download_mt3dms():
    # Remove the existing target download directory if it exists
    if os.path.isdir(mtusgspth):
        shutil.rmtree(mtusgspth)

    pm.target = "mt3dms"
    pm.download_target(pm.target, download_path=dstpth)
    assert pm.download, f"could not download {pm.target} distribution"


@pytest.mark.base
@pytest.mark.regression
def test_compile_mt3dms():
    assert pm.build() == 0, f"could not compile {pm.target}"


@pytest.mark.base
@pytest.mark.regression
def test_download():
    # Remove the existing target download directory if it exists
    if os.path.isdir(mtusgspth):
        shutil.rmtree(mtusgspth)

    # reset the Pymake object for target
    pm.reset(target)

    # download the target
    pm.download_target(target, download_path=dstpth)
    assert pm.download, f"could not download {target} distribution"


@pytest.mark.base
@pytest.mark.regression
def test_compile():
    assert pm.build() == 0, f"could not compile {target}"


@pytest.mark.regression
@pytest.mark.skipif(sys.platform == "darwin", reason="do not run on OSX")
def test_download_exes():
    pymake.getmfexes(dstpth, exes=("mfnwt", "mf6"), verbose=True)
    return


@pytest.mark.regression
@pytest.mark.skipif(sys.platform == "darwin", reason="do not run on OSX")
@pytest.mark.skipif(sys.platform == "win32", reason="do not run on Windows")
@pytest.mark.parametrize("ws", sim_dirs)
def test_mt3dusgs(ws):
    assert run_mt3dusgs(ws), f"could not run {ws}"


@pytest.mark.base
@pytest.mark.regression
def test_clean_up():
    clean_up()


if __name__ == "__main__":
    test_download_mt3dms()
    test_compile_mt3dms()
    test_download_exes()
    test_download()
    test_compile()
    for dn in sim_dirs:
        run_mt3dusgs(dn)
    test_clean_up()
