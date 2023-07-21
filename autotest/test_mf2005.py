import sys
from pathlib import Path

import flopy
import pytest

import pymake


@pytest.fixture(scope="module")
def target(module_tmpdir) -> Path:
    target = "mf2005"
    if sys.platform.lower() == "win32":
        target += ".exe"
    return module_tmpdir / target


@pytest.fixture(scope="module")
def prog_data(target) -> dict:
    return pymake.usgs_program_data.get_target(target.name)


@pytest.fixture(scope="module")
def workspace(module_tmpdir, prog_data) -> Path:
    return module_tmpdir / prog_data.dirname


@pytest.fixture(scope="module")
def pm(module_tmpdir, target) -> pymake.Pymake:
    pm = pymake.Pymake(verbose=True)
    pm.target = str(target)
    pm.appdir = str(module_tmpdir)
    pm.fflags = "-O3"
    pm.cflags = "-O3"
    yield pm
    pm.finalize()


def run_mf2005(namefile, ws, exe):
    print(f"running model {namefile} using {exe}")
    success, _ = flopy.run_model(exe, namefile, model_ws=ws, silent=False)
    return success


@pytest.mark.dependency(name="download")
@pytest.mark.base
def test_download(pm, module_tmpdir, target):
    pm.download_target(target, download_path=module_tmpdir)
    assert pm.download, f"could not download {target}"


@pytest.mark.dependency(name="build", depends=["download"])
@pytest.mark.base
def test_compile(pm, target):
    assert pm.build() == 0, f"could not compile {target}"


@pytest.mark.dependency(name="test", depends=["build"])
@pytest.mark.regression
@pytest.mark.parametrize(
    "namefile",
    [
        "l1b2k_bath.nam",
        "test1tr.nam",
        "mnw1.nam",
        "testsfr2.nam",
        "bcf2ss.nam",
        "restest.nam",
        "etsdrt.nam",
        "str.nam",
        "tr2k_s3.nam",
        "fhb.nam",
        "twri.nam",
        "ibs2k.nam",
        "swtex4.nam",
        "twrihfb.nam",
        "l1a2k.nam",
        "tc2hufv4.nam",
        "twrip.nam",
        "l1b2k.nam",
        "test1ss.nam",
    ],
)
def test_mf2005(namefile, workspace, target):
    example_ws = workspace / "test-run"
    if not (example_ws / namefile).is_file():
        pytest.skip(f"{namefile} does not exist")

    success, _ = flopy.run_model(
        target, namefile, model_ws=example_ws, silent=False
    )
    assert success, f"could not run {namefile} with {target}"
