import os
import sys
import shutil
import pymake
import flopy

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

# set up pths and exes
epths = [emp7, emf2005, emfusg, emf6]


def download_src():
    # Remove the existing target download directory if it exists
    if os.path.isdir(mp7pth):
        shutil.rmtree(mp7pth)

    # download the target
    pm.download_target(target, download_path=dstpth)


def get_simfiles():
    if os.path.exists(emp7):
        edirs = [
            name
            for name in os.listdir(expth)
            if os.path.isdir(os.path.join(expth, name))
        ]
        pths = [os.path.join(expth, edir) for edir in edirs]
        dirs = []
        for pth in pths:
            for name in os.listdir(pth):
                if os.path.isdir(os.path.join(pth, name)):
                    dirs.append(os.path.join(pth, name))
        simfiles = []
        for d in dirs:
            pth = os.path.join(d, "original")
            simfiles += [
                os.path.join(pth, f)
                for f in os.listdir(pth)
                if f.endswith(".mpsim")
            ]
    else:
        simfiles = [None]
    return simfiles


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
            assert success, "could not run...{}".format(msg)

        # run the modpath model
        print("running model...{}".format(fn))
        exe = emp7

        fpth = os.path.basename(fn)
        success, buff = flopy.run_model(
            exe, fpth, model_ws=model_ws, silent=False
        )
        if not success:
            errmsg = "could not run {}".format(os.path.basename(fn))
    else:
        success = False
        errmsg = "could not run...{}".format(emp7)

    assert success, errmsg
    return


def clean_up():
    print("Removing temporary build directories")
    dirs_temp = [os.path.join("obj_temp"), os.path.join("mod_temp")]
    for d in dirs_temp:
        if os.path.isdir(d):
            shutil.rmtree(d)

    # remove download directory
    pm.download_cleanup()

    # clean up compiled executables
    for epth in epths:
        if os.path.isfile(epth):
            print("Removing...'" + epth + "'")
            os.remove(epth)
    return


def test_download():
    download_src()


def test_compile():
    pm.build()


def test_download_exes():
    pymake.getmfexes(dstpth, exes=("mf2005", "mfusg", "mf6"), verbose=True)


def test_modpath7():
    simfiles = get_simfiles()
    for fn in simfiles:
        yield run_modpath7, fn


def test_clean_up():
    clean_up()


if __name__ == "__main__":
    test_download()
    test_compile()
    test_download_exes()
    for fn in get_simfiles():
        run_modpath7(fn)
    test_clean_up()
