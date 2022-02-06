import os
import shutil
import sys
import time

import flopy
import pytest

import pymake

# define program data
target = "mf6"
if sys.platform.lower() == "win32":
    target += ".exe"

sharedobject_target = "libmf6"
if sys.platform.lower() == "win32":
    sharedobject_target += ".dll"
elif sys.platform.lower() == "darwin":
    sharedobject_target += ".dylib"
else:
    sharedobject_target += ".so"

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join(f"temp_{os.path.basename(__file__).replace('.py', '')}")
if not os.path.exists(dstpth):
    os.makedirs(dstpth, exist_ok=True)

mf6ver = prog_dict.version
mf6pth = os.path.join(dstpth, prog_dict.dirname)
epth = os.path.join(dstpth, target)

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

pm = pymake.Pymake(verbose=True)
pm.target = target
pm.appdir = dstpth
pm.makefile = True
pm.makeclean = True
pm.inplace = True
pm.networkx = True
pm.meson = True


def build_with_makefile(makefile_target):
    success = False
    if os.path.isfile("makefile"):
        # wait to delete on windows
        if sys.platform.lower() == "win32":
            time.sleep(6)

        print("Removing temporary build directories")
        dirs_temp = [
            os.path.join("src_temp"),
            os.path.join("obj_temp"),
            os.path.join("mod_temp"),
        ]
        for d in dirs_temp:
            if os.path.isdir(d):
                shutil.rmtree(d)

        # clean prior to make
        print(f"clean {makefile_target} with makefile")
        os.system("make clean")

        # build MODFLOW 6 with makefile
        print(f"build {makefile_target} with makefile")
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
            success = os.path.isfile(os.path.join(dstpth, makefile_target))

    return success


def clean_up():
    # clean up makefile
    print("Removing makefile")
    files = ["makefile", "makedefaults"]
    for fpth in files:
        if os.path.isfile(fpth):
            os.remove(fpth)

    # finalize pymake object
    pm.finalize()

    if os.path.isfile(epth):
        print("Removing " + target)
        os.remove(epth)

    print("Removing temporary build directories")
    dirs_temp = [dstpth]
    for d in dirs_temp:
        if os.path.isdir(d):
            shutil.rmtree(d)
    return


def run_mf6(ws):
    success = False
    exe_name = os.path.abspath(epth)
    if os.path.exists(exe_name):
        # run test models
        print(f"running model...{os.path.basename(ws)}")
        success, buff = flopy.run_model(
            exe_name, None, model_ws=ws, silent=False
        )
    return success


@pytest.mark.base
@pytest.mark.regression
def test_download():
    # Remove the existing mf6 directory if it exists
    if os.path.isdir(mf6pth):
        shutil.rmtree(mf6pth)

    # download the modflow 6 release
    pm.download_target(target, download_path=dstpth)
    assert pm.download, f"could not download {target} distribution"


@pytest.mark.base
@pytest.mark.regression
def test_compile():
    assert pm.build() == 0, f"could not compile {target}"


@pytest.mark.regression
@pytest.mark.parametrize("ws", sim_dirs)
def test_mf6(ws):
    assert run_mf6(ws), f"could not run {ws}"


@pytest.mark.base
@pytest.mark.regression
def test_makefile():
    assert build_with_makefile(
        target
    ), f"could not compile {target} with makefile"


@pytest.mark.base
@pytest.mark.regression
def test_sharedobject():
    pm.target = sharedobject_target
    prog_dict = pymake.usgs_program_data.get_target(pm.target)
    pm.appdir = dstpth
    pm.srcdir = os.path.join(mf6pth, prog_dict.srcdir)
    pm.srcdir2 = os.path.join(mf6pth, "src")
    pm.excludefiles = [os.path.join(pm.srcdir2, "mf6.f90")]
    pm.makefile = True
    pm.makeclean = True
    pm.sharedobject = True
    pm.inplace = True
    pm.dryrun = True
    assert pm.build() == 0, f"could not compile {pm.target}"


@pytest.mark.base
@pytest.mark.regression
def test_sharedobject_makefile():
    assert build_with_makefile(
        sharedobject_target
    ), f"could not compile {sharedobject_target} with makefile"


@pytest.mark.base
@pytest.mark.regression
def test_clean_up():
    clean_up()


if __name__ == "__main__":
    test_download()
    test_compile()
    for ws in sim_dirs:
        run_mf6(ws)
    test_makefile()
    test_sharedobject()
    test_sharedobject_makefile()
    test_clean_up()
