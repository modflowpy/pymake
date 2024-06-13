import os
import shutil
from pathlib import Path
from platform import system

import flopy
import pytest
from modflow_devtools.misc import set_dir

import pymake


@pytest.fixture(scope="module")
def target(module_tmpdir) -> Path:
    name = "mp6"
    ext = ".exe" if system() == "Windows" else ""
    return module_tmpdir / f"{name}{ext}"


@pytest.fixture(scope="module")
def prog_data(target) -> dict:
    return pymake.usgs_program_data.get_target(target.name)


@pytest.fixture(scope="module")
def workspace(module_tmpdir, prog_data) -> Path:
    return module_tmpdir / f"temp/{prog_data.dirname}"


def update_files(fn, workspace):
    # rename a few files for linux
    replace_files = ["example-6", "example-7", "example-8"]
    for rf in replace_files:
        if rf in fn.lower():
            fname1 = workspace / f"{rf}.locations"
            fname2 = workspace / f"{rf}_mod.locations"
            print(
                "copy {} to {}".format(
                    os.path.basename(fname1), os.path.basename(fname2)
                )
            )
            shutil.copy(fname1, fname2)
            print(f"deleting {os.path.basename(fname1)}")
            os.remove(fname1)
            fname1 = workspace / f"{rf.upper()}.locations"
            print(
                "renmae {} to {}".format(
                    os.path.basename(fname2), os.path.basename(fname1)
                )
            )
            os.rename(fname2, fname1)


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
    "namefile", [f"EXAMPLE-{n}.mpsim" for n in range(1, 10)]
)
def test_mp6(namefile, workspace, target):
    example_ws = workspace / "example-run"
    if not (example_ws / namefile).is_file():
        pytest.skip(f"Namefile {namefile} does not exist")

    update_files(namefile, example_ws)
    success, _ = flopy.run_model(
        target, namefile, model_ws=example_ws, silent=False
    )
    assert success, f"could not run {namefile}"
