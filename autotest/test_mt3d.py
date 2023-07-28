import os
import sys
from pathlib import Path

import flopy
import pytest

import pymake


@pytest.fixture(scope="module")
def target(module_tmpdir) -> Path:
    return module_tmpdir / "mt3dusgs"


@pytest.fixture(scope="module")
def prog_data(target) -> dict:
    return pymake.usgs_program_data.get_target(target.name)


@pytest.fixture(scope="module")
def workspace(module_tmpdir, prog_data) -> Path:
    return module_tmpdir / prog_data.dirname


@pytest.fixture(scope="module")
def pm(module_tmpdir) -> pymake.Pymake:
    pm = pymake.Pymake(verbose=True)
    pm.appdir = str(module_tmpdir)
    pm.makeclean = True
    yield pm
    pm.finalize()


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


@pytest.mark.dependency(name="download_mt3dms")
@pytest.mark.base
def test_download_mt3dms(pm, module_tmpdir):
    pm.target = "mt3dms"
    pm.download_target(pm.target, download_path=module_tmpdir)
    assert pm.download, f"could not download {pm.target} distribution"


@pytest.mark.dependency(name="build_mt3dms", depends=["download_mt3dms"])
@pytest.mark.base
def test_compile_mt3dms(pm):
    assert pm.build() == 0, f"could not compile {pm.target}"


@pytest.mark.dependency(name="download")
@pytest.mark.base
def test_download(pm, module_tmpdir, target):
    pm.reset(str(target))
    pm.download_target(target, download_path=module_tmpdir)
    assert pm.download, f"could not download {target} distribution"


@pytest.mark.dependency(name="build", depends=["download"])
@pytest.mark.base
def test_compile(pm, target):
    assert pm.build() == 0, f"could not compile {target}"


@pytest.mark.regression
@pytest.mark.skipif(sys.platform == "darwin", reason="do not run on OSX")
def test_download_exes(module_tmpdir):
    pymake.getmfexes(module_tmpdir, exes=("mfnwt", "mf6"), verbose=True)


@pytest.mark.regression
@pytest.mark.skipif(sys.platform == "darwin", reason="do not run on OSX")
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
def test_mt3dusgs(module_tmpdir, workspace, ws, target):
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
