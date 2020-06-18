from __future__ import print_function
import os
import sys
import shutil
import pymake

# define program data
target = 'mfnwt'
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

        tepth = epth
        if sys.platform.lower() == 'win32':
            tepth += '.exe'

        # remove existing target
        if os.path.isfile(target):
            print('Removing ' + target)
            os.remove(target)

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
        assert os.path.isfile(target), errmsg
    else:
        print('makefile does not exist...skipping build_with_make()')
    return


def clean_up():
    # clean up make file
    files = ['makefile', 'makedefaults']
    print('Removing makefile and temporary build directories')
    for fpth in files:
        if os.path.isfile(fpth):
            os.remove(fpth)
    dirs_temp = [os.path.join('obj_temp'),
                 os.path.join('mod_temp')]
    for d in dirs_temp:
        if os.path.isdir(d):
            shutil.rmtree(d)

    # clean up MODFLOW-NWT download
    if os.path.isdir(mfnwtpth):
        print('Removing folder ' + mfnwtpth)
        shutil.rmtree(mfnwtpth)

    tepth = target
    if sys.platform == 'win32':
        tepth += '.exe'

    # clean up MODFLOW-NWT
    if os.path.isfile(tepth):
        print('Removing ' + target)
        os.remove(tepth)

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
