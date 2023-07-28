import os
import sys
import time
from platform import system
from pathlib import Path

import flopy
import pytest
from modflow_devtools.misc import set_dir

import pymake

# set fpth based on current path
if os.path.basename(os.path.normpath(os.getcwd())) == "autotest":
    fpth = os.path.abspath(
        os.path.join("temp", "mf6examples", "mf6examples.txt")
    )
else:
    fpth = os.path.abspath(
        os.path.join("autotest", "temp", "mf6examples", "mf6examples.txt")
    )
if os.path.isfile(fpth):
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
def target_so(module_tmpdir) -> Path:
    sharedobject_target = "libmf6"
    if sys.platform.lower() == "win32":
        sharedobject_target += ".dll"
    elif sys.platform.lower() == "darwin":
        sharedobject_target += ".dylib"
    else:
        sharedobject_target += ".so"
    return module_tmpdir / sharedobject_target


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


def build_with_makefile(pm, workspace, exe):
    exe_path = Path(exe)
    success = False
    with set_dir(workspace):
        if os.path.isfile("makefile"):
            # wait to delete on windows
            if sys.platform.lower() == "win32":
                time.sleep(6)

            # clean prior to make
            print(f"clean {exe} with makefile")
            os.system("make clean")

            # build MODFLOW 6 with makefile
            print(f"build {exe} with makefile")
            return_code = os.system("make")

            # test if running on Windows with ifort, if True the makefile
            # should fail
            if sys.platform.lower() == "win32" and pm.fc == "ifort":
                if return_code != 0:
                    success = True
                else:
                    success = False
            # verify that target was made
            else:
                success = exe_path.is_file()

    return success


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
def test_mf6(ws, target):
    success, _ = flopy.run_model(target, None, model_ws=ws, silent=False)
    assert success, f"could not run {ws}"


@pytest.mark.dependency(name="makefile", depends=["build"])
@pytest.mark.base
def test_makefile(pm, module_tmpdir, target):
    assert build_with_makefile(
        pm, module_tmpdir, target
    ), f"could not compile {target} with makefile"


@pytest.mark.dependency(name="shared", depends=["makefile"])
@pytest.mark.base
def test_sharedobject(pm, module_tmpdir, workspace, target_so, prog_data):
    # reconfigure pymake object
    pm.target = str(target_so)
    pm.appdir = module_tmpdir
    pm.srcdir = workspace / prog_data.srcdir
    pm.srcdir2 = workspace / "src"
    pm.excludefiles = [os.path.join(pm.srcdir2, "mf6.f90")]
    pm.makefile = True
    pm.makeclean = True
    pm.sharedobject = True
    pm.inplace = True
    pm.dryrun = False

    # build the target
    assert pm.build() == 0, f"could not compile {pm.target}"
    assert target_so.is_file()


@pytest.mark.dependency(name="shared_makefile", depends=["shared", "makefile"])
@pytest.mark.base
def test_sharedobject_makefile(pm, module_tmpdir, target_so):
    assert build_with_makefile(
        pm, module_tmpdir, target_so
    ), f"could not compile {target_so} with makefile"
