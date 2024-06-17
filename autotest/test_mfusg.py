import os
from pathlib import Path
from platform import system

import flopy
import pytest

import pymake


@pytest.fixture(scope="module")
def targets(module_tmpdir):
    ext = ".exe" if system() == "Windows" else ""
    return [module_tmpdir / f"{name}{ext}" for name in ["mfusg", "mfusg_gsi"]]


@pytest.fixture(scope="module")
def prog_data(targets) -> dict:
    return pymake.usgs_program_data.get_target(targets[0].name)


@pytest.fixture(scope="module")
def workspace(module_tmpdir, prog_data) -> Path:
    return module_tmpdir / prog_data.dirname


@pytest.fixture(scope="module")
def pm(module_tmpdir, targets) -> pymake.Pymake:
    pm = pymake.Pymake(verbose=True)
    pm.target = str(targets[0])
    pm.appdir = str(module_tmpdir)
    yield pm
    pm.finalize()


@pytest.fixture(scope="module")
def pm_gsi(module_tmpdir, targets) -> pymake.Pymake:
    pm_gsi = pymake.Pymake(verbose=True)
    pm_gsi.target = str(targets[1])
    pm_gsi.appdir = str(module_tmpdir)
    yield pm_gsi
    pm_gsi.finalize()


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


def run_mfusg(fn, exe):
    success, _ = flopy.run_model(
        exe, os.path.basename(fn), model_ws=os.path.dirname(fn), silent=False
    )
    errmsg = f"could not run {fn} with {exe}"
    assert success, errmsg


@pytest.mark.dependency(name="download")
@pytest.mark.xdist_group("mfusg")
@pytest.mark.regression
def test_download(pm, pm_gsi, module_tmpdir, targets):
    pm.download_target(targets[0], download_path=module_tmpdir)
    assert pm.download, f"could not download {targets[0]}"

    pm_gsi.download_target(targets[1], download_path=module_tmpdir)
    assert pm_gsi.download, f"could not download {targets[1]}"


@pytest.mark.dependency(name="build", depends=["download"])
@pytest.mark.xdist_group("mfusg")
@pytest.mark.regression
def test_compile(pm, pm_gsi, targets):
    assert pm.build() == 0, f"could not compile {targets[0]}"
    assert (targets[0]).is_file()

    assert pm_gsi.build() == 0, f"could not compile {targets[1]}"
    assert targets[1].is_file()


@pytest.mark.dependency(name="test", depends=["download", "build"])
@pytest.mark.xdist_group("mfusg")
@pytest.mark.regression
@pytest.mark.parametrize(
    "namefile",
    [
        "01A_nestedgrid_nognc/flow.nam",
        "01B_nestedgrid_gnc/flow.nam",
        "03A_conduit_unconfined/ex3A.nam",
        "03B_conduit_unconfined/ex3B.nam",
        "03C_conduit_unconfined/ex3C.nam",
        "03D_conduit_unconfined/ex3D.nam",
        "03_conduit_confined/ex3.nam",
    ],
)
def test_mfusg(workspace, namefile, targets):
    namefile_path = workspace / "test" / namefile
    edit_namefile(namefile_path)
    run_mfusg(namefile_path, targets[0])
    run_mfusg(namefile_path, targets[1])
