from __future__ import print_function
import os
import sys
import time
import shutil
import pymake
import flopy

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

pm = pymake.Pymake()


def get_example_dirs():
    exclude_dir = []
    # remove after MODFLOW 6 v6.1.2 release
    if sys.platform.lower() == 'win32':
        exclude_dir = ['ex34-csub-sub01']
    if os.path.isdir(expth):
        exdirs = sorted([o for o in os.listdir(expth)
                         if os.path.isdir(os.path.join(expth, o)) and
                         o not in exclude_dir])
    else:
        exdirs = [None]
    return exdirs


def download_mf6():
    # Remove the existing mf6 directory if it exists
    if os.path.isdir(mf6pth):
        shutil.rmtree(mf6pth)

    # download the modflow 6 release
    pm.download_target(target, download_path=dstpth)


def compile_code():
    # compile MODFLOW 6
    pymake.usgs_program_data().list_targets(current=True)
    pm.build(target=target, appdir=dstpth, dryrun=False, makefile=True)


def build_with_makefile():
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
        errmsg = "{} created by makefile does not exist.".format(target)
        success = os.path.isfile(epth)
    else:
        errmsg = "makefile does not exist...skipping build_with_make()"
        success = False

    assert success, errmsg

    return


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

    # remove download directory
    pm.download_cleanup()

    if os.path.isfile(epth):
        print("Removing " + target)
        os.remove(epth)
    return


def run_mf6(ws):
    exe_name = os.path.abspath(epth)
    if os.path.exists(exe_name):
        print("running...{}".format(ws))
        # setup
        src = os.path.join(expth, ws)
        dst = os.path.join(dstpth, ws)
        pymake.setup_mf6(src, dst)

        # run test models
        print("running model...{}".format(os.path.basename(ws)))
        success, buff = flopy.run_model(
            exe_name, None, model_ws=dst, silent=False
        )
        if not success:
            errmsg = "could not run {}".format(os.path.basename(ws))
    else:
        success = False
        errmsg = "could not run {}".format(exe_name)

    if success:
        pymake.teardown(dst)

    assert success, errmsg

    return


def test_download():
    download_mf6()


def test_compile():
    compile_code()


def test_mf6():
    # get name files and simulation name
    example_dirs = get_example_dirs()
    # run models
    for ws in example_dirs:
        yield run_mf6, ws


def test_makefile():
    build_with_makefile()


def test_clean_up():
    yield clean_up


if __name__ == "__main__":
    # download MODFLOW 6
    download_mf6()

    # compile MODFLOW 6
    compile_code()

    # get name files and simulation name
    example_dirs = get_example_dirs()

    # # run models
    # for ws in example_dirs:
    #     run_mf6(ws)

    # build modflow 6 with a pymake generated makefile
    build_with_makefile()

    # clean up
    clean_up()
