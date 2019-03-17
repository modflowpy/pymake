from __future__ import print_function
import os
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
                         replace_function=replace_function)


def build_with_makefile():
    if os.path.isfile('makefile'):

        # remove existing target
        print('Removing ' + target)
        os.remove(epth)

        print('Removing temporary build directories')
        shutil.rmtree(os.path.join('src_temp'))
        shutil.rmtree(os.path.join('obj_temp'))
        shutil.rmtree(os.path.join('mod_temp'))

        # build MODFLOW-NWT with makefile
        print('build {} with makefile'.format(target))
        os.system('make')
        assert os.path.isfile(epth), \
            '{} created by makefile does not exist.'.format(target)
    else:
        print('makefile does not exist...skipping build_with_make()')
    return


def clean_up():
    # clean up make file
    if os.path.isfile('makefile'):
        print('Removing makefile and temporary build directories')
        shutil.rmtree(os.path.join('obj_temp'))
        os.remove('makefile')

    # clean up MODFLOW-NWT
    if os.path.isfile(epth):
        print('Removing ' + target)
        os.remove(epth)

    # clean up MODFLOW-NWT download
    if os.path.isdir(mfnwtpth):
        print('Removing folder ' + mfnwtpth)
        shutil.rmtree(mfnwtpth)

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
