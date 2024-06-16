import os
import sys
from pathlib import Path

import flopy
import pytest
from modflow_devtools.misc import set_dir

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
    return module_tmpdir / f"temp/{prog_data.dirname}"


def run_mf2005(namefile, ws, exe):
    print(f"running model {namefile} using {exe}")
    success, _ = flopy.run_model(exe, namefile, model_ws=ws, silent=False)
    return success


@pytest.mark.dependency(name="build")
@pytest.mark.regression
def test_compile(module_tmpdir, target):
    cc = os.environ.get("CC", "gcc")
    fc = os.environ.get("FC", "gfortran")
    pymake.linker_update_environment(cc=cc, fc=fc)
    with set_dir(module_tmpdir):
        assert (
            pymake.build_apps(
                target.stem,
                verbose=True,
                clean=False,
                meson=True,
            )
            == 0
        ), f"could not compile {target.stem}"


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
