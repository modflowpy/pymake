import os
import sys
import time
from pathlib import Path
from platform import system

import flopy
import pytest
from modflow_devtools.misc import set_dir

import pymake

# set fpth based on current path
if os.path.basename(os.path.normpath(os.getcwd())) == "autotest":
    fpth = Path("temp")
else:
    fpth = Path("autotest/temp")
fpth = (fpth / "mf6examples/mf6examples.txt").resolve()
if fpth.is_file():
    with open(fpth) as f:
        lines = f.read().splitlines()
    sim_dirs = [line for line in lines if len(line) > 0]
else:
    sim_dirs = []


@pytest.fixture(scope="module")
def target(module_tmpdir) -> Path:
    name = "mf6"
    ext = ".exe" if system() == "Windows" else ""
    return module_tmpdir / f"{name}{ext}"


@pytest.fixture(scope="module")
def prog_data(target) -> dict:
    return pymake.usgs_program_data.get_target(target.name)


@pytest.fixture(scope="module")
def workspace(module_tmpdir, prog_data) -> Path:
    return module_tmpdir / f"temp/{prog_data.dirname}"


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
@pytest.mark.parametrize("ws", sim_dirs)
def test_mf6(ws, target):
    success, _ = flopy.run_model(target, None, model_ws=ws, silent=False)
    assert success, f"could not run {ws}"
