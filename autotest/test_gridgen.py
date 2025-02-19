import subprocess
from os import environ
from pathlib import Path
from platform import system

import pytest

import pymake

TARGET_NAME = "gridgen"


@pytest.fixture(scope="module")
def target(module_tmpdir) -> Path:
    name = TARGET_NAME
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
    pm.appdir = str(module_tmpdir)
    pm.cc = environ.get("CXX", "g++")
    pm.fc = None
    pm.inplace = True
    pm.makeclean = True
    yield pm
    pm.finalize()


def run_command(args, cwd):
    p = subprocess.Popen(
        args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd
    )
    for line in p.stdout.readlines():
        print(line.decode().strip())
    retval = p.wait()
    return retval


def run_gridgen(cmd, ws, exe):
    args = [str(exe)] + cmd.split()
    print(f"running {' '.join(args)}")
    return run_command(args, ws) == 0


@pytest.mark.dependency(name="download")
@pytest.mark.xdist_group(TARGET_NAME)
@pytest.mark.regression
def test_download(pm, module_tmpdir, target):
    pm.download_target(target, download_path=module_tmpdir)
    assert pm.download, f"could not download {target} distribution"


@pytest.mark.dependency(name="build", depends=["download"])
@pytest.mark.xdist_group(TARGET_NAME)
@pytest.mark.regression
def test_compile(pm, target):
    assert pm.build() == 0, f"could not compile {target}"


@pytest.mark.dependency(name="test", depends=["build"])
@pytest.mark.xdist_group(TARGET_NAME)
@pytest.mark.regression
@pytest.mark.parametrize(
    "cmd",
    [
        "buildqtg action01_buildqtg.dfn",
        "grid02qtg-to-usgdata action02_writeusgdata.dfn",
        "grid01mfg-to-polyshapefile action03_shapefile.dfn",
        "grid02qtg-to-polyshapefile action03_shapefile.dfn",
        "grid01mfg-to-pointshapefile action03_shapefile.dfn",
        "grid02qtg-to-pointshapefile action03_shapefile.dfn",
        "canal_grid02qtg_lay1_intersect action04_intersect.dfn",
        "chd_grid02qtg_lay1_intersect action04_intersect.dfn",
        "grid01mfg-to-vtkfile action05_vtkfile.dfn",
        "grid02qtg-to-vtkfile action05_vtkfile.dfn",
        "grid02qtg-to-vtkfilesv action05_vtkfile.dfn",
    ],
)
def test_gridgen(cmd, workspace, target):
    assert run_gridgen(
        cmd, workspace / "examples" / "biscayne", target
    ), f"could not run {cmd}"
