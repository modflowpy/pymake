import os
import pathlib as pl
import subprocess
from platform import system

import pytest
from modflow_devtools.misc import set_dir

import pymake


@pytest.fixture(scope="module")
def target(module_tmpdir) -> pl.Path:
    name = "gridgen"
    ext = ".exe" if system() == "Windows" else ""
    return module_tmpdir / f"{name}{ext}"


@pytest.fixture(scope="module")
def prog_data(target) -> dict:
    return pymake.usgs_program_data.get_target(target.name)


@pytest.fixture(scope="module")
def workspace(module_tmpdir, prog_data) -> pl.Path:
    return module_tmpdir / f"temp/{prog_data.dirname}"


def run_command(args, cwd):
    p = subprocess.Popen(
        args,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=cwd,
    )
    for line in p.stdout.readlines():
        print(line.decode().strip())
    retval = p.wait()
    return retval


def run_gridgen(cmd, ws, exe):
    args = [str(exe)] + cmd.split()
    print(f"running {' '.join(args)}")
    return run_command(args, ws) == 0


@pytest.mark.dependency(name="build")
@pytest.mark.regression
def test_compile(module_tmpdir, target):
    cc = os.environ.get("CC", "g++")
    fc = None
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
def test_gridgen(module_tmpdir, cmd, workspace, target):
    assert run_gridgen(
        cmd, workspace / "examples" / "biscayne", module_tmpdir / target
    ), f"could not run {cmd}"
