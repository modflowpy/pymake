import os
import sys
from pathlib import Path
from platform import system

import flopy
import pytest
from modflow_devtools.misc import set_dir

import pymake

APPS = ["mt3dms", "mt3dusgs"]
EXT = ".exe" if system() == "Windows" else ""


@pytest.fixture(scope="module")
def prog_data() -> dict:
    return pymake.usgs_program_data.get_target("mt3dusgs")


@pytest.fixture(scope="module")
def workspace(module_tmpdir, prog_data) -> Path:
    return module_tmpdir / f"temp/{prog_data.dirname}"


def run_mt3dusgs(workspace, mt3dms_exe, mfnwt_exe, mf6_exe):
    success = False
    model_ws = workspace

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
    msg = f"{mfnwt_exe}"
    if mf_nam is not None:
        msg += f" {os.path.basename(mf_nam)}"
    if flow_model == "mfnwt":
        nam = mf_nam
        eapp = mfnwt_exe
    elif flow_model == "mf6":
        nam = None
        eapp = mf6_exe
    success, _ = flopy.run_model(eapp, nam, model_ws=model_ws, silent=False)

    # run the MT3D-USGS model
    if success:
        print(f"running model...{mt_nam}")
        success, _ = flopy.run_model(
            mt3dms_exe,
            mt_nam,
            model_ws=model_ws,
            silent=False,
            normal_msg="Program completed.",
        )

    return success


@pytest.mark.dependency(name="build")
@pytest.mark.regression
@pytest.mark.parametrize(
    "target",
    APPS,
)
def test_compile(module_tmpdir, target):
    target_path = module_tmpdir / f"{target}{EXT}"
    cc = os.environ.get("CC", "gcc")
    fc = os.environ.get("FC", "gfortran")
    pymake.linker_update_environment(cc=cc, fc=fc)
    with set_dir(module_tmpdir):
        assert (
            pymake.build_apps(
                target,
                verbose=True,
                clean=False,
                meson=True,
            )
            == 0
        ), f"could not compile {target}"


@pytest.mark.dependency(
    name="download_exes",
    depends=[
        "build",
    ],
)
@pytest.mark.regression
# @pytest.mark.skipif(sys.platform == "darwin", reason="do not run on OSX")
def test_download_exes(module_tmpdir):
    pymake.getmfexes(module_tmpdir, exes=("mfnwt", "mf6"), verbose=True)


@pytest.mark.dependency(name="test", depends=["build", "download_exes"])
@pytest.mark.regression
# @pytest.mark.skipif(sys.platform == "darwin", reason="do not run on OSX")
@pytest.mark.skipif(sys.platform == "win32", reason="do not run on Windows")
@pytest.mark.parametrize(
    "ws",
    [
        "2ED5EAs",
        "CTS1",
        "CTS2",
        "CTS3",
        "CTS4",
        "Keating",
        "Keating_UZF",
        "SFT_CrnkNic",
        # "UZT_Disp_Lamb01_TVD",
        # "UZT_Disp_Lamb1",
        # "UZT_Disp_Lamb10",
        # "UZT_NonLin",
        "gwt",
        "lkt",
        "p01SpatialStresses(mf6)",
    ],
)
def test_mt3dusgs(module_tmpdir, workspace, ws):
    target = module_tmpdir / f"{APPS[1]}{EXT}"
    mfnwt_exe = module_tmpdir / "mfnwt"
    if pymake.usgs_program_data().get_version(mfnwt_exe) == "1.2.0":
        exclude = [
            "UZT_NonLin",
            "UZT_Disp_Lamb01_TVD",
            "UZT_Disp_Lamb1",
            "UZT_Disp_Lamb10",
        ]
        if ws in exclude:
            pytest.skip(reason="excluding {ws}")

    exclude = [
        "Keating",
        "Keating_UZF",
    ]
    if ws in exclude:
        pytest.skip(reason="excluding {ws}")

    assert run_mt3dusgs(
        workspace / "data" / ws,
        target,
        mfnwt_exe,
        module_tmpdir / "mf6",
    ), f"could not run {ws}"
