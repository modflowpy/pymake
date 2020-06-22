from __future__ import print_function
import os
import sys
import shutil
import pymake

# define program data
target = 'mfnwt'
if sys.platform.lower() == 'win32':
    target += '.exe'

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join('temp')
if not os.path.exists(dstpth):
    os.makedirs(dstpth)

mfnwtpth = os.path.join(dstpth, prog_dict.dirname)

srcpth = os.path.join(mfnwtpth, prog_dict.srcdir)
epth = os.path.join(dstpth, target)


def compile_code():
    # Remove the existing MODFLOW-NWT directory if it exists
    if os.path.isdir(mfnwtpth):
        shutil.rmtree(mfnwtpth)

    # compile MODFLOW-NWT
    replace_function = pymake.build_replace(target)
    pymake.build_program(target=target,
                         download_dir=dstpth,
                         makeclean=False,
                         makefile=True,
                         exe_dir=dstpth,
                         dryrun=False,
                         replace_function=replace_function)


def build_with_makefile():
    if os.path.isfile('makefile'):
        # remove existing target
        if os.path.isfile(epth):
            print('Removing ' + target)
            os.remove(epth)

        print('Removing temporary build directories')
        dirs_temp = [os.path.join('src_temp'),
                     os.path.join('obj_temp'),
                     os.path.join('mod_temp')]
        for d in dirs_temp:
            if os.path.isdir(d):
                shutil.rmtree(d)

        # build MODFLOW-NWT with makefile
        print('build {} with makefile'.format(target))
        os.system('make')

        # verify that MODFLOW-NWT was made
        errmsg = '{} created by makefile does not exist.'.format(target)
        success = os.path.isfile(epth)
    else:
        errmsg = 'makefile does not exist...skipping build_with_make()'

    assert success, errmsg

    return


def clean_up():
    # clean up make file
    print('Removing makefile')
    files = ['makefile', 'makedefaults']
    for fpth in files:
        if os.path.isfile(fpth):
            os.remove(fpth)

    print('Removing temporary build directories')
    dirs_temp = [os.path.join('obj_temp'),
                 os.path.join('mod_temp')]
    for d in dirs_temp:
        if os.path.isdir(d):
            shutil.rmtree(d)

    # clean up MODFLOW-NWT download
    if os.path.isdir(mfnwtpth):
        print('Removing folder ' + mfnwtpth)
        shutil.rmtree(mfnwtpth)

    # clean up MODFLOW-NWT
    if os.path.isfile(epth):
        print('Removing ' + target)
        os.remove(epth)

    return


def test_compile():
    # compile MODFLOW-NWT
    compile_code()


def test_makefile():
    build_with_makefile()


def test_clean_up():
    clean_up()


if __name__ == "__main__":
    compile_code()
    build_with_makefile()
    clean_up()
