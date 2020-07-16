import os
import sys
import shutil

import pymake
import flopy

# define program data
target = "swtv4"
if sys.platform.lower() == "win32":
    target += ".exe"

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join("temp")
if not os.path.exists(dstpth):
    os.makedirs(dstpth)

swtpth = os.path.join(dstpth, prog_dict.dirname)
expth = os.path.join(swtpth, "examples")
deppth = os.path.join(swtpth, "dependencies")

srcpth = os.path.join(swtpth, prog_dict.srcdir)
epth = os.path.abspath(os.path.join(dstpth, target))

pm = pymake.Pymake(verbose=True)
pm.target = target
pm.appdir = dstpth
pm.double = True


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
        f.write("{}\n".format(line))
    f.close()


def get_namefiles():
    if os.path.exists(epth):
        exclude_tests = ("7_swtv4_ex", "6_rotation")
        namefiles = pymake.get_namefiles(expth, exclude=exclude_tests)
        simname = pymake.get_sim_name(namefiles, rootpth=expth)
    else:
        namefiles = [None]
        simname = [None]
    return zip(namefiles, simname)


def download_src():
    # Remove the existing seawat directory if it exists
    if os.path.isdir(swtpth):
        shutil.rmtree(swtpth)

    # download the target
    pm.download_target(target, download_path=dstpth)


def clean_up():
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


def run_seawat(namepth, dst):
    if namepth is not None:
        print("running...{}".format(dst))
        # setup
        testpth = os.path.join(dstpth, dst)
        pymake.setup(namepth, testpth)

        # edit name file
        pth = os.path.join(testpth, os.path.basename(namepth))
        edit_namefile(pth)

        # run test models
        if os.path.exists(epth):
            print("running model...{}".format(os.path.basename(namepth)))
            success, buff = flopy.run_model(
                epth, os.path.basename(namepth), model_ws=testpth, silent=False
            )
        if success:
            pymake.teardown(testpth)
        else:
            errmsg = "could not run...{}".format(os.path.basename(namepth))
    else:
        success = False
        errmsg = "{} does not exist".format(epth)

    assert success, errmsg

    return


def build_seawat_dependency_graphs():
    if os.path.exists(epth):

        # build dependencies output directory
        if not os.path.exists(deppth):
            os.makedirs(deppth)

        # build dependency graphs
        print("building dependency graphs")
        pymake.visualize.make_plots(srcpth, deppth, verbose=True)

        # test that the dependency figure for the SEAWAT main exists
        findf = os.path.join(deppth, "swt_v4.f.png")
        success = os.path.isfile(findf)
        assert success, "could not find {}".format(findf)
    else:
        success = False

    assert success, "could not build dependency graphs"

    return


def test_download():
    download_src()


def test_compile():
    pm.build()


def test_seawat():
    # get name files and simulation name
    namefiles = get_namefiles()

    # run models
    for namepth, dst in namefiles:
        yield run_seawat, namepth, dst


def test_dependency_graphs():
    build_seawat_dependency_graphs()


def test_clean_up():
    clean_up()


if __name__ == "__main__":
    test_download()
    test_compile()
    for namepth, dst in get_namefiles():
        run_seawat(namepth, dst)
    test_dependency_graphs()
    test_clean_up()
