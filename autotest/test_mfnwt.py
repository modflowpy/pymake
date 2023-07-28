import os
import sys
import time
from pathlib import Path

import pytest
from modflow_devtools.misc import set_dir

import pymake


@pytest.fixture(scope="module")
def target(module_tmpdir) -> str:
    target = "mfnwt"
    return module_tmpdir / target


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
    pm.makefile = True
    pm.makefiledir = str(module_tmpdir)
    pm.inplace = True
    pm.dryrun = False
    pm.verbose = True
    yield pm
    pm.finalize()


def build_with_makefile(ws):
    success = True
    with set_dir(ws):
        if os.path.isfile("makefile"):
            # wait to delete on windows
            if sys.platform.lower() == "win32":
                time.sleep(6)

            # clean prior to make
            print(f"clean {target} with makefile")
            os.system("make clean")

            # build MODFLOW-NWT with makefile
            print(f"build {target} with makefile")
            return_code = os.system("make")

            # test if running on Windows with ifort, if True the makefile
            # should fail
            errmsg = f"{target} created by makefile does not exist."
            if sys.platform.lower() == "win32" and pm.fc == "ifort":
                if return_code != 0:
                    success = True
                else:
                    success = False
            # verify that MODFLOW-NWT was made
            else:
                success = os.path.isfile(target)
        else:
            errmsg = "makefile does not exist"

    assert success, errmsg


@pytest.mark.dependency(name="download")
@pytest.mark.base
def test_download(pm, module_tmpdir, target):
    pm.download_target(target, download_path=module_tmpdir)
    assert pm.download, f"could not download {target} distribution"


@pytest.mark.dependency(name="build", depends=["download"])
@pytest.mark.base
def test_compile(pm, target):
    assert pm.build() == 0, f"could not compile {target}"


@pytest.mark.dependency(name="makefile", depends=["build"])
@pytest.mark.base
def test_makefile(workspace):
    build_with_makefile(workspace)
