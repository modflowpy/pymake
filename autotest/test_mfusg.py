import os
from pathlib import Path
from platform import system

import flopy
import pytest
from modflow_devtools.misc import set_dir

import pymake

APPS = ["mfusg", "mfusg_gsi"]
EXT = ".exe" if system() == "Windows" else ""


@pytest.fixture(scope="module")
def targets(module_tmpdir):
    ext = ".exe" if system() == "Windows" else ""
    return [module_tmpdir / f"{name}{ext}" for name in ["mfusg", "mfusg_gsi"]]


@pytest.fixture(scope="module")
def prog_data(targets) -> dict:
    return pymake.usgs_program_data.get_target(targets[0].name)


@pytest.fixture(scope="module")
def workspace(module_tmpdir, prog_data) -> Path:
    return module_tmpdir / f"temp/{prog_data.dirname}"


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


@pytest.mark.dependency(name="build")
@pytest.mark.regression
@pytest.mark.parametrize(
    "target",
    APPS,
)
def test_compile(module_tmpdir, target):
    target_path = module_tmpdir / f"{target}{EXT}"
    cc = os.environ.get("CC", "gcc")
    fc = os.environ.get("FC", "gfortran")
    pymake.linker_update_environment(cc=cc, fc=fc)
    with set_dir(module_tmpdir):
        assert (
            pymake.build_apps(
                target,
                verbose=True,
                clean=False,
                meson=True,
            )
            == 0
        ), f"could not compile {target}"


@pytest.mark.dependency(name="test", depends=["build"])
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
@pytest.mark.parametrize(
    "target",
    APPS,
)
def test_mfusg(module_tmpdir, workspace, namefile, target):
    target_path = module_tmpdir / f"{target}{EXT}"
    namefile_path = workspace / "test" / namefile
    edit_namefile(namefile_path)
    run_mfusg(namefile_path, target_path)
