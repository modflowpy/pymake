import os
import sys
import time
import shutil
import pymake
import flopy

import pytest

# define program data
target = "mf6"
if sys.platform.lower() == "win32":
    target += ".exe"

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join("temp")
if not os.path.exists(dstpth):
    os.makedirs(dstpth)

mf6ver = prog_dict.version
mf6pth = os.path.join(dstpth, prog_dict.dirname)
expth = os.path.join(mf6pth, "examples")
epth = os.path.join(dstpth, target)

sim_dirs = [
    "ex01-twri",
    "ex02-tidal",
    "ex03-bcf2ss",
    "ex04-fhb",
    "ex05-mfusg1disu",
    "ex06-mfusg1disv",
    "ex07-mfusg1lgr",
    "ex08-mfusg1xt3d",
    "ex09-bump",
    "ex10-bumpnr",
    "ex11-disvmesh",
    "ex12-hanicol",
    "ex13-hanirow",
    "ex14-hanixt3d",
    "ex15-whirlsxt3d",
    "ex16-mfnwt2",
    "ex17-mfnwt3h",
    "ex18-mfnwt3l",
    "ex19-zaidel",
    "ex20-keating",
    "ex21-sfr1",
    "ex22-lak2",
    "ex23-lak4",
    "ex24-neville",
    "ex25-flowing-maw",
    "ex26-Reilly-maw",
    "ex27-advpakmvr",
    "ex28-mflgr3",
    "ex29-vilhelmsen-gc",
    "ex30-vilhelmsen-gf",
    "ex31-vilhelmsen-lgr",
    "ex32-periodicbc",
    "ex33-csub-jacob",
    "ex34-csub-sub01",
    "ex35-csub-holly",
    "ex36-csub-subwt01",
    "ex37-draindepth",
]

# remove after MODFLOW 6 v6.1.2 release
if sys.platform.lower() == "win32":
    for exclude in ("ex34-csub-sub01",):
        if exclude in sim_dirs:
            sim_dirs.remove(exclude)

# add path to sim_dirs
for idx, simdir in enumerate(sim_dirs):
    sim_dirs[idx] = os.path.join(expth, simdir)

pm = pymake.Pymake(verbose=True)
pm.target = target
pm.appdir = dstpth
pm.dryrun = False
pm.makefile = True
pm.inplace = True


def build_with_makefile():
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
        print("clean {} with makefile".format(target))
        os.system("make clean")

        # build MODFLOW 6 with makefile
        print("build {} with makefile".format(target))
        os.system("make")

        # verify that MODFLOW 6 was made
        success = os.path.isfile(epth)

    return success


def clean_up():
    # clean up makefile
    print("Removing makefile")
    files = ["makefile", "makedefaults"]
    for fpth in files:
        if os.path.isfile(fpth):
            os.remove(fpth)

    print("Removing temporary build directories")
    dirs_temp = [os.path.join("obj_temp"), os.path.join("mod_temp")]
    for d in dirs_temp:
        if os.path.isdir(d):
            shutil.rmtree(d)

    # finalize pymake object
    pm.finalize()

    if os.path.isfile(epth):
        print("Removing " + target)
        os.remove(epth)
    return


def run_mf6(ws):
    success = False
    exe_name = os.path.abspath(epth)
    if os.path.exists(exe_name):
        # run test models
        print("running model...{}".format(os.path.basename(ws)))
        success, buff = flopy.run_model(
            exe_name, None, model_ws=ws, silent=False
        )
    return success


def test_download():
    # Remove the existing mf6 directory if it exists
    if os.path.isdir(mf6pth):
        shutil.rmtree(mf6pth)

    # download the modflow 6 release
    pm.download_target(target, download_path=dstpth)
    assert pm.download, "could not download {} distribution".format(target)


def test_compile():
    assert pm.build() == 0, "could not compile {}".format(target)


@pytest.mark.parametrize("ws", sim_dirs)
def test_mf6(ws):
    assert run_mf6(ws), "could not run {}".format(ws)


def test_makefile():
    assert build_with_makefile(), "could not compile {} with makefile".format(
        target
    )


def test_sharedobject():
    pm.target = "libmf6"
    prog_dict = pymake.usgs_program_data.get_target(pm.target)
    pm.srcdir = os.path.join(mf6pth, prog_dict.srcdir)
    pm.srcdir2 = os.path.join(mf6pth, "src")
    pm.excludefiles = [os.path.join(pm.srcdir2, "mf6.f90")]
    pm.makefile = False
    pm.sharedobject = True
    pm.inplace = False
    assert pm.build() == 0, "could not compile {}".format(pm.target)


def test_clean_up():
    clean_up()


if __name__ == "__main__":
    test_download()
    test_compile()
    for ws in sim_dirs:
        run_mf6(ws)
    test_makefile()
    test_sharedobject()
    test_clean_up()
