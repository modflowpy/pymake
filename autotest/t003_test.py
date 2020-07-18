import os
import sys
import shutil
import pymake
import flopy

# define program data
target = "mfusg"
if sys.platform.lower() == "win32":
    target += ".exe"

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join("temp")
if not os.path.exists(dstpth):
    os.makedirs(dstpth)

mfusgpth = os.path.join(dstpth, prog_dict.dirname)
expth = os.path.join(mfusgpth, "test")

srcpth = os.path.join(mfusgpth, prog_dict.srcdir)
epth = os.path.abspath(os.path.join(dstpth, target))

pm = pymake.Pymake(verbose=True)
pm.target = target
pm.appdir = dstpth


def edit_namefiles():
    namefiles = pymake.get_namefiles(expth)
    for namefile in namefiles:
        # read existing namefile
        f = open(namefile, "r")
        lines = f.read().splitlines()
        f.close()
        # convert file extensions to lower case
        f = open(namefile, "w")
        for line in lines:
            t = line.split()
            fn, ext = os.path.splitext(t[2])
            f.write(
                "{:15s} {:3s} {} ".format(
                    t[0], t[1], "{}{}".format(fn, ext.lower())
                )
            )
            if len(t) > 3:
                f.write("{}".format(t[3]))
            f.write("\n")
        f.close()


def get_namefiles():
    if os.path.exists(epth):
        exclude_tests = ("7_swtv4_ex",)
        namefiles = pymake.get_namefiles(expth, exclude=exclude_tests)
        simname = pymake.get_sim_name(namefiles, rootpth=expth)
    else:
        namefiles = [None]
        simname = [None]

    return zip(namefiles, simname)


def download_src():
    # Remove the existing mf2005 directory if it exists
    if os.path.isdir(mfusgpth):
        shutil.rmtree(mfusgpth)

    # download the modflow 2005 release
    pm.download_target(target, download_path=dstpth)


def clean_up():
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


def run_mfusg(namepth, dst):
    if os.path.exists(epth):
        # setup
        testpth = os.path.join(dstpth, dst)
        pymake.setup(namepth, testpth)

        # run test models
        print("running model...{}".format(os.path.basename(namepth)))
        success, buff = flopy.run_model(
            epth, os.path.basename(namepth), model_ws=testpth, silent=True
        )
        if success:
            pymake.teardown(testpth)
        else:
            errmsg = "could not run {}".format(os.path.basename(namepth))
    else:
        success = False
        errmsg = "could not run {}".format(epth)

    assert success, errmsg

    return


def test_download():
    download_src()


def test_compile():
    pm.build()

    return


def test_mfusg():
    # edit namefiles
    edit_namefiles()
    # get name files and simulation name
    sim_list = get_namefiles()
    # run models
    for namepth, dst in sim_list:
        yield run_mfusg, namepth, dst


def test_clean_up():
    yield clean_up


if __name__ == "__main__":
    test_download()

    test_compile()

    # edit namefiles
    edit_namefiles()

    # get name files and simulation name
    sim_list = get_namefiles()

    # run models
    for namepth, dst in sim_list:
        run_mfusg(namepth, dst)

    # clean up
    test_clean_up()
