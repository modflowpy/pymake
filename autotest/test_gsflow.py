import os
from pathlib import Path
from platform import system

import flopy
import pytest

import pymake

# set fpth based on current path
if os.path.basename(os.path.normpath(os.getcwd())) == "autotest":
    fpth = Path("temp")
else:
    fpth = Path("autotest/temp")
fpth = (fpth / "gsflowexamples/gsflowexamples.txt").resolve()
if fpth.is_file():
    with open(fpth) as f:
        lines = f.read().splitlines()
    sim_dirs = [line for line in lines if len(line) > 0]
else:
    sim_dirs = []


@pytest.fixture(scope="module")
def target(module_tmpdir) -> Path:
    name = "gsflow"
    ext = ".exe" if system() == "Windows" else ""
    return module_tmpdir / f"{name}{ext}"


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
    pm.appdir = module_tmpdir
    pm.makefile = True
    pm.makeclean = True
    pm.makefiledir = module_tmpdir
    pm.inplace = True
    pm.networkx = True
    pm.verbose = True
    yield pm
    pm.finalize()


@pytest.mark.dependency(name="download")
@pytest.mark.base
def test_download(pm, module_tmpdir, target):
    pm.download_target(target, download_path=module_tmpdir)
    assert pm.download, f"could not download {target} distribution"


@pytest.mark.dependency(name="build", depends=["download"])
@pytest.mark.base
def test_compile(pm, target):
    assert pm.build() == 0, f"could not compile {target}"


@pytest.mark.dependency(name="test", depends=["build"])
@pytest.mark.regression
@pytest.mark.parametrize("ws", sim_dirs)
def test_gsflow(ws, target):
    success, _ = flopy.run_model(
        target,
        "gsflow.control",
        model_ws=ws,
        silent=False,
        normal_msg=[
            "normal termination",
            "Normal completion of GSFLOW",
        ],
    )
    assert success, f"could not run {ws}"
