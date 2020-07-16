import os
import sys
import shutil
import pymake
import flopy

# define program data
target = "gsflow"
if sys.platform.lower() == "win32":
    target += ".exe"

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join("temp")
if not os.path.exists(dstpth):
    os.makedirs(dstpth)

gsflowver = prog_dict.version
gsflowpth = os.path.join(dstpth, prog_dict.dirname)
egsflow = os.path.abspath(os.path.join(dstpth, target))

# example path
expth = os.path.join(gsflowpth, "data")
examples = ["sagehen"]
control_files = ["gsflow.control"]

# set up pths and exes
pths = [gsflowpth]
exes = [egsflow]

pm = pymake.Pymake(verbose=True)
pm.target = target
pm.appdir = dstpth


def download_src():
    # Remove the existing target download directory if it exists
    if os.path.isdir(gsflowpth):
        shutil.rmtree(gsflowpth)

    # download the target
    pm.download_target(target, download_path=dstpth)


def copy_example_dir(epth):
    if os.path.exists(egsflow):
        src = os.path.join(expth, epth)
        dst = os.path.join(dstpth, epth)

        # delete dst if it exists
        if os.path.isdir(dst):
            shutil.rmtree(dst)

        # copy the files
        try:
            shutil.copytree(src, dst)
        except:
            msg = "could not move files from {} to '{}'".format(src, dst)
            raise NameError(msg)

        # edit the control file for a shorter run
        # sagehen
        if epth == examples[0]:
            fpth = os.path.join(dstpth, epth, "linux", control_files[0])
            with open(fpth) as f:
                lines = f.readlines()
            with open(fpth, "w") as f:
                idx = 0
                while idx < len(lines):
                    line = lines[idx]
                    if "end_time" in line:
                        line += "6\n1\n1981\n"
                        idx += 3
                    f.write(line)
                    idx += 1
    return


def run_gsflow(example, control_file):
    if os.path.exists(egsflow):
        # copy files
        copy_example_dir(example)

        model_ws = os.path.join(dstpth, example, "linux")

        # run the flow model
        success, buff = flopy.run_model(
            egsflow, control_file, model_ws=model_ws, silent=False
        )
        if not success:
            errmsg = "could not run {}".format(control_file)
    else:
        success = False
        errmsg = "could not run...{}".format(egsflow)

    assert success, errmsg

    return


def clean_up():
    # clean up downloaded directories
    if os.path.isdir(gsflowpth):
        print("Removing folder " + gsflowpth)
        shutil.rmtree(gsflowpth)

    # clean up examples
    for example in examples:
        pth = os.path.join(dstpth, example)
        if os.path.isdir(pth):
            print("Removing example folder " + example)
            shutil.rmtree(pth)

    # remove download directory
    pm.download_cleanup()

    # clean up compiled executables
    if os.path.isfile(egsflow):
        print("Removing...'" + egsflow + "'")
        os.remove(egsflow)
    return


def test_download():
    download_src()


def test_compile():
    pm.build()


def test_gsflow():
    for ex, cf in zip(examples, control_files):
        yield run_gsflow, ex, cf


def test_clean_up():
    clean_up()
    return


if __name__ == "__main__":
    test_download()
    test_compile()
    for ex, cf in zip(examples, control_files):
        run_gsflow(ex, cf)
    test_clean_up()
