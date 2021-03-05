import os
import sys
import shutil
import pymake
import flopy

import pytest

# define program data
target = "mp7"
if sys.platform.lower() == "win32":
    target += ".exe"

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join("temp")
if not os.path.exists(dstpth):
    os.makedirs(dstpth)

mp7pth = os.path.join(dstpth, prog_dict.dirname)
emp7 = os.path.abspath(os.path.join(dstpth, target))

mf2005_target = "mf2005"
emf2005 = os.path.abspath(os.path.join(dstpth, mf2005_target))

mfusg_target = "mfusg"
emfusg = os.path.abspath(os.path.join(dstpth, mfusg_target))

mf6_target = "mf6"
emf6 = os.path.abspath(os.path.join(dstpth, mf6_target))

if sys.platform.lower() == "win32":
    emf2005 += ".exe"
    emfusg += ".exe"
    emf6 += ".exe"

pm = pymake.Pymake(verbose=True)
pm.target = target
pm.appdir = dstpth

# MODPATH 7 examples
expth = os.path.join(mp7pth, "examples")

name_files = [
    "ex01/modflow-2005/original/ex01a_mf2005.mpsim",
    "ex01/modflow-2005/original/ex01b_mf2005.mpsim",
    "ex01/modflow-6/original/ex01a_mf6.mpsim",
    "ex01/modflow-6/original/ex01b_mf6.mpsim",
    "ex02/modflow-6/original/ex02a_mf6.mpsim",
    "ex02/modflow-6/original/ex02b_mf6.mpsim",
    "ex02/modflow-usg/original/ex02a_mfusg.mpsim",
    "ex02/modflow-usg/original/ex02b_mfusg.mpsim",
    "ex03/modflow-6/original/ex03a_mf6.mpsim",
    "ex04/modflow-6/original/ex04a_mf6.mpsim",
]
# add path to name_files
for idx, namefile in enumerate(name_files):
    name_files[idx] = os.path.join(expth, namefile)

# set up pths and exes
epths = [emp7, emf2005, emfusg, emf6]


def replace_data(dpth):
    fpths = [
        name
        for name in os.listdir(dpth)
        if os.path.isfile(os.path.join(dpth, name))
    ]
    repl = False
    if "ex01_mf2005.dis" in fpths:
        sfinds = ["! Example 1: MODFLOW-2005 discretization file"]
        srepls = ["# Example 1: MODFLOW-2005 discretization file\n"]
        fpth = "ex01_mf2005.dis"
        repl = True
    elif "ex04_mf6.disv" in fpths:
        sfinds = ["  OPEN/CLOSE  mptest006_idomain.csv"]
        srepls = ["  OPEN/CLOSE  ex04_mf6_idomain.csv\n"]
        fpth = "ex04_mf6.disv"
        repl = True
    elif "mfsim.nam" in fpths:
        sfinds = [
            "  TDIS6  ex02a_mf6.tdis",
            "  GWF6  ex02a_mf6.nam  ex02a_mf6",
            "  IMS6  ex02a_mf6.ims  ex02a_mf6",
        ]
        srepls = [
            "  TDIS6  ex02_mf6.tdis\n",
            "  GWF6  ex02_mf6.nam  ex02_mf6\n",
            "  IMS6  ex02_mf6.ims  ex02_mf6\n",
        ]
        fpth = "mfsim.nam"
        repl = True
    if repl:
        fpth = os.path.join(dpth, fpth)
        with open(fpth, "r") as f:
            content = f.readlines()
        for idx, line in enumerate(content):
            for jdx, sfind in enumerate(sfinds):
                if sfind in line:
                    content[idx] = line.replace(line, srepls[jdx])
        with open(fpth, "w") as f:
            f.writelines(content)
    return


def set_lowercase(fpth):
    with open(fpth, "r") as f:
        content = f.readlines()
    for idx, line in enumerate(content):
        content[idx] = line.lower()
    with open(fpth, "w") as f:
        f.writelines(content)
    return


def run_modpath7(fn):
    success = False
    if os.path.exists(emp7):
        model_ws = os.path.dirname(fn)
        # run the flow model
        run = True
        if "modflow-2005" in fn.lower():
            exe = emf2005
            v = flopy.which(exe)
            if v is None:
                run = False
            nam = [
                name for name in os.listdir(model_ws) if ".nam" in name.lower()
            ]
            if len(nam) > 0:
                fpth = nam[0]
                # read and rewrite the name file
                set_lowercase(os.path.join(model_ws, fpth))
            else:
                fpth = None
                run = False
        elif "modflow-usg" in fn.lower():
            exe = emfusg
            v = flopy.which(exe)
            if v is None:
                run = False
            nam = [
                name for name in os.listdir(model_ws) if ".nam" in name.lower()
            ]
            if len(nam) > 0:
                fpth = nam[0]
            else:
                fpth = None
                run = False
        elif "modflow-6" in fn.lower():
            exe = emf6
            v = flopy.which(exe)
            if v is None:
                run = False
            fpth = None
        else:
            run = False
        if run:
            # fix any known problems
            replace_data(model_ws)
            # run the model
            msg = "{}".format(exe)
            if fpth is not None:
                msg += " {}".format(os.path.basename(fpth))
            success, buff = flopy.run_model(
                exe, fpth, model_ws=model_ws, silent=False
            )

        if success:
            # run the modpath model
            print("running model...{}".format(fn))
            exe = emp7

            fpth = os.path.basename(fn)
            success, buff = flopy.run_model(
                exe, fpth, model_ws=model_ws, silent=False
            )

    return success


def clean_up():
    print("Removing temporary build directories")
    dirs_temp = [os.path.join("obj_temp"), os.path.join("mod_temp")]
    for d in dirs_temp:
        if os.path.isdir(d):
            shutil.rmtree(d)

    # finalize pymake object
    pm.finalize()

    # clean up compiled executables
    for epth in epths:
        if os.path.isfile(epth):
            print("Removing...'" + epth + "'")
            os.remove(epth)
    return


@pytest.mark.base
@pytest.mark.regression
def test_download():
    # Remove the existing target download directory if it exists
    if os.path.isdir(mp7pth):
        shutil.rmtree(mp7pth)

    # download the target
    pm.download_target(target, download_path=dstpth)
    assert pm.download, "could not download {} distribution".format(target)


@pytest.mark.base
@pytest.mark.regression
def test_compile():
    assert pm.build() == 0, "could not compile {}".format(target)


@pytest.mark.regression
def test_download_exes():
    pymake.getmfexes(dstpth, exes=("mf2005", "mfusg", "mf6"), verbose=True)


@pytest.mark.regression
@pytest.mark.parametrize("fn", name_files)
def test_modpath7(fn):
    assert run_modpath7(fn), "could not run {}".format(fn)


@pytest.mark.base
@pytest.mark.regression
def test_clean_up():
    clean_up()


if __name__ == "__main__":
    # test_download()
    # test_compile()
    # test_download_exes()
    for fn in name_files:
        run_modpath7(fn)
    # test_clean_up()
