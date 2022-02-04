import os
import shutil

import pytest

import pymake

# define program data
target = "mflgr"

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join(".", "temp")
if not os.path.exists(dstpth):
    os.makedirs(dstpth)

mflgrpth = os.path.join(dstpth, prog_dict.dirname)


def compile_code():
    # Remove the existing mfusg directory if it exists
    if os.path.isdir(mflgrpth):
        shutil.rmtree(mflgrpth)

    # compile MODFLOW-LGR
    return pymake.build_apps(
        target, download_dir=dstpth, appdir=dstpth, verbose=True
    )


def clean_up():
    # clean up download directory
    print("Removing folder " + mflgrpth)
    if os.path.isdir(mflgrpth):
        shutil.rmtree(mflgrpth)

    # get list of files with target in name
    epths = []
    for file in os.listdir(dstpth):
        fpth = os.path.join(dstpth, file)
        if os.path.isfile(fpth):
            if target in file:
                epths.append(fpth)

    # clean up the executable
    for epth in epths:
        print("removing...'" + epth + "'")
        os.remove(epth)

    return


@pytest.mark.base
def test_compile():
    assert compile_code() == 0, f"could not compile {target}"


@pytest.mark.base
def test_clean_up():
    clean_up()


if __name__ == "__main__":
    compile_code()
    clean_up()
