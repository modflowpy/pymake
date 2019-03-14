from __future__ import print_function
import os
import shutil
import pymake

# define program data
target = 'mflgr'
prog_dict = pymake.usgs_prog_data().get_target_data(target)

# set up paths
dstpth = os.path.join('.', 'temp')
if not os.path.exists(dstpth):
    os.makedirs(dstpth)

mflgrpth = os.path.join(dstpth, prog_dict.dirname)
expth = os.path.join(mflgrpth, 'test')

srcpth = os.path.join(mflgrpth, prog_dict.srcdir)
epth = os.path.join(dstpth, target)


def compile_code():
    # Remove the existing mfusg directory if it exists
    if os.path.isdir(mflgrpth):
        shutil.rmtree(mflgrpth)

    # compile MODFLOW-LGR
    replace_function = pymake.build_replace(target)
    pymake.build_program(target=target,
                         download_dir=dstpth,
                         exe_dir=dstpth,
                         replace_function=replace_function)

    return


def clean_up():
    # clean up download directory
    print('Removing folder ' + mflgrpth)
    shutil.rmtree(mflgrpth)

    # clean up the executable
    print('Removing ' + target)
    os.remove(epth)
    return

    return


def test_compile():
    # compile MFLGR
    compile_code()


def test_clean_up():
    yield clean_up


if __name__ == "__main__":
    compile_code()
    clean_up()
