import os
import subprocess
import sys
from pathlib import Path
from platform import system
from shutil import copytree
from typing import Tuple

import flopy
import pytest

import pymake


_system = system()
_eext = ".exe" if _system == "Windows" else ""

_prms_name = "prms"
_prms_dict = pymake.usgs_program_data.get_target(_prms_name)
_prms_ver = _prms_dict.version
_prms_examples = (
    (
        "sagehen",
        os.path.join("control", "sagehen.control"),
    ),
    (
        "acf",
        os.path.join("control", "acf.control"),
    ),
)

_triangle_name = "triangle"
_triangle_dict = pymake.usgs_program_data.get_target(_triangle_name)
_triangle_ver = _triangle_dict.version

_gridgen_name = "gridgen"
_gridgen_dict = pymake.usgs_program_data.get_target(_gridgen_name)
_gridgen_ver = _gridgen_dict.version
_gridgen_examples_path = Path(_gridgen_dict.dirname) / "examples"
_gridgen_examples = [_gridgen_examples_path / "biscayne"]
_gridgen_biscayne_cmds = [
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
]


def run_command(cmdlist, cwd):
    p = subprocess.Popen(
        cmdlist,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=cwd,
    )
    for line in p.stdout.readlines():
        print(line.decode().strip())
    retval = p.wait()
    return retval


@pytest.fixture
def prms_setup(tmp_path_factory) -> Tuple[pymake.Pymake, Path, Path]:
    target = _prms_name
    if sys.platform.lower() == "win32":
        target += ".exe"

    wrkdir = tmp_path_factory.mktemp("prms_setup")

    pm = pymake.Pymake(verbose=True)
    pm.target = target
    pm.appdir = os.path.join(wrkdir, "bin")
    pm.makeclean = True
    pm.meson = True
    pm.mesondir = os.path.join(wrkdir)

    # download prms
    pm.download_target(target, download_path=str(wrkdir))

    dir_path = Path(wrkdir) / _prms_dict.dirname
    exe_path = (dir_path / "bin" / target).absolute()

    # make sure prms is executable
    assert exe_path.is_file()
    exe_path.chmod(exe_path.stat().st_mode | 0o111)

    yield pm, dir_path, exe_path

    pm.finalize()


@pytest.fixture
def gridgen_setup(tmp_path_factory) -> Tuple[pymake.Pymake, Path, Path]:
    target = _gridgen_name
    # todo: requesting 'gridgen' returns gridgen.exe in bin dir, should it?
    # if sys.platform.lower() == "win32":
    target += ".exe"

    wrkdir = tmp_path_factory.mktemp("gridgen_setup")

    pm = pymake.Pymake(verbose=True)
    pm.target = target
    pm.appdir = os.path.join(wrkdir, "bin")
    pm.makeclean = True
    pm.meson = True
    pm.mesondir = os.path.join(wrkdir)

    cc = os.environ.get("CC")
    if cc is not None:
        pm.cc = cc
    else:
        pm.cc = "g++"
    pm.fc = None

    # download gridgen
    print(target)
    pm.download_target(target, download_path=str(wrkdir))

    from pprint import pprint
    pprint(list(wrkdir.rglob('**')))

    dir_path = Path(wrkdir) / _gridgen_dict.dirname
    exe_path = (dir_path / "bin" / target).absolute()

    # make sure gridgen is executable
    assert exe_path.is_file()
    exe_path.chmod(exe_path.stat().st_mode | 0o111)

    yield pm, dir_path, exe_path

    pm.finalize()


@pytest.fixture
def triangle_setup(tmp_path_factory):
    target = _triangle_name
    if sys.platform.lower() == "win32":
        target += ".exe"

    wrkdir = tmp_path_factory.mktemp("triangle_setup")

    pm = pymake.Pymake(verbose=True)
    pm.target = _triangle_name
    pm.appdir = os.path.join(wrkdir, "bin")
    pm.inplace = True
    pm.meson = True
    pm.mesondir = os.path.join(wrkdir)

    # download triangle
    pm.download_target(_triangle_name, download_path=str(wrkdir))

    dir_path = Path(wrkdir) / _triangle_dict.dirname
    exe_path = (dir_path / "bin" / target).absolute()

    # make sure triangle is executable
    # assert exe_path.is_file()
    # exe_path.chmod(exe_path.stat().st_mode | 0o111)

    yield pm, dir_path, exe_path

    pm.finalize()


@pytest.mark.base
@pytest.mark.regression
def test_download_prms(prms_setup):
    pm, dir_path, exe_path = prms_setup
    assert pm.download, f"failed to download {_prms_name}"


@pytest.mark.base
@pytest.mark.regression
def test_compile_prms(prms_setup):
    pm, dir_path, exe_path = prms_setup
    assert pm.build() == 0, f"failed to compile {_prms_name}"


@pytest.mark.regression
@pytest.mark.parametrize("ex,cf", _prms_examples)
def test_run_prms(prms_setup, tmp_path, ex, cf):
    pm, dir_path, exe_path = prms_setup
    model_ws = os.path.join(tmp_path, ex)

    copytree(Path(dir_path) / "projects" / ex, tmp_path / ex)

    success, buff = flopy.run_model(
        str(exe_path),
        str(Path(dir_path) / "projects" / ex / cf),
        model_ws=model_ws,
        silent=False,
        normal_msg=f"Normal completion of {_prms_name}",
    )
    assert success, f"failed to run {_prms_name} {cf}"


@pytest.mark.base
@pytest.mark.regression
def test_download_triangle(triangle_setup, tmp_path):
    pm, dir_path, exe_path = triangle_setup
    assert pm.download, f"failed to download {_triangle_name}"


@pytest.mark.base
@pytest.mark.regression
def test_compile_triangle(triangle_setup, tmp_path):
    pm, dir_path, exe_path = triangle_setup
    assert pm.build() == 0, f"failed to compile {_triangle_name}"


@pytest.mark.base
@pytest.mark.regression
def test_download_gridgen(gridgen_setup, tmp_path):
    pm, dir_path, exe_path = gridgen_setup
    assert pm.download, f"failed to download {_gridgen_name} distribution"


@pytest.mark.base
@pytest.mark.regression
def test_compile_gridgen(gridgen_setup):
    pm, dir_path, exe_path = gridgen_setup
    assert pm.build() == 0, f"failed to compile {_gridgen_name}"


@pytest.mark.skipif(_system != "Windows", reason="needs Windows while .exe is always retrieved")
@pytest.mark.regression
@pytest.mark.parametrize("cmd", _gridgen_biscayne_cmds)
@pytest.mark.parametrize("ex", _gridgen_examples)
def test_run_gridgen(gridgen_setup, tmp_path, cmd, ex):
    pm, dir_path, exe_path = gridgen_setup
    cmdlist = [str(exe_path)] + cmd.split()
    print(f"running {' '.join(cmdlist)}")
    retcode = run_command(cmdlist, dir_path.parent / ex)
    assert retcode == 0, f"failed to run {exe_path}"
