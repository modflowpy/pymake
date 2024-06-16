import os
import sys
from pathlib import Path
from platform import system

import flopy
import pytest
from modflow_devtools.misc import is_in_ci

import pymake


@pytest.fixture(scope="module")
def target(module_tmpdir) -> Path:
    name = "swtv4"
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
    pm.double = True
    yield pm
    # pm.finalize()


def edit_namefile(namefile):
    # read existing namefile
    f = open(namefile, "r")
    lines = f.read().splitlines()
    f.close()
    # remove global line
    f = open(namefile, "w")
    for line in lines:
        if "global" in line.lower():
            continue
        f.write(f"{line}\n")
    f.close()


def build_seawat_dependency_graphs(src_path, dep_path):
    success = True
    build_graphs = True
    if is_in_ci():
        if "linux" not in sys.platform.lower():
            build_graphs = False

    if build_graphs:
        # build dependencies output directory
        if not os.path.exists(dep_path):
            os.makedirs(dep_path, exist_ok=True)

        # build dependency graphs
        print("building dependency graphs")
        # todo support pathlike, not just str?
        pymake.make_plots(str(src_path), dep_path, verbose=True)

        # test that the dependency figure for the SEAWAT main exists
        findf = dep_path / "swt_v4.f.png"
        assert findf.is_file(), f"could not find {findf}"

    assert success, "could not build dependency graphs"


@pytest.mark.dependency(name="download")
@pytest.mark.regression
def test_download(pm, module_tmpdir, target):
    pm.download_target(target, download_path=module_tmpdir)
    assert pm.download, f"could not download {target}"


@pytest.mark.dependency(name="build", depends=["download"])
@pytest.mark.regression
def test_compile(pm, target):
    assert pm.build() == 0, f"could not compile {target}"


@pytest.mark.dependency(name="test", depends=["build"])
@pytest.mark.regression
@pytest.mark.parametrize(
    "namefile",
    sorted(
        [
            "4_hydrocoin/seawat.nam",
            "5_saltlake/seawat.nam",
            "2_henry/1_classic_case1/seawat.nam",
            "2_henry/4_VDF_uncpl_Trans/seawat.nam",
            "2_henry/5_VDF_DualD_Trans/seawat.nam",
            "2_henry/6_age_simulation/henry_mod.nam",
            "2_henry/2_classic_case2/seawat.nam",
            "2_henry/3_VDF_no_Trans/seawat.nam",
            "1_box/case1/seawat.nam",
            "1_box/case2/seawat.nam",
            "3_elder/seawat.nam",
        ]
    ),
)
def test_seawat(namefile, workspace, target):
    namefile_path = workspace / "examples" / namefile
    edit_namefile(namefile_path)

    success, _ = flopy.run_model(
        target,
        os.path.basename(namefile_path),
        model_ws=os.path.dirname(namefile_path),
        silent=False,
    )
    assert success, f"could not run...{os.path.basename(namefile_path)}"


@pytest.mark.dependency(name="graph", depends=["test"])
@pytest.mark.regression
def test_dependency_graphs(workspace, prog_data):
    src_path = workspace / prog_data.srcdir
    dep_path = workspace / "dependencies"
    build_seawat_dependency_graphs(src_path, dep_path)
