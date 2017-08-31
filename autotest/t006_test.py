from __future__ import print_function
import os
import shutil
import pymake
from pymake.download import download_and_unzip

# set up paths
dstpth = os.path.join('temp')
if not os.path.exists(dstpth):
    os.makedirs(dstpth)
mfnwtpth = os.path.join(dstpth, 'MODFLOW-NWT_1.1.2')

exe_name = 'mfnwt'
srcpth = os.path.join(mfnwtpth, 'src')
target = os.path.join(dstpth, exe_name)


def compile_code():
    # Remove the existing directory if it exists
    if os.path.isdir(mfnwtpth):
        shutil.rmtree(mfnwtpth)

    # Download the MODFLOW-NWT distribution
    url = "https://water.usgs.gov/ogw/modflow-nwt/MODFLOW-NWT_1.1.3.zip"
    download_and_unzip(url, pth=dstpth)

    pymake.main(srcpth, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=False, debug=False,
                makefile=True)

    assert os.path.isfile(target), 'Target does not exist.'


def build_with_makefile():
    if os.path.isfile('makefile'):
        # remove existing target
        print('Removing ' + target)
        os.remove(target)
        print('build mfnwt with makefile')
        os.system('make')
        assert os.path.isfile(target), \
            'Target created by makefile does not exist.'
    else:
        print('makefile does not exist...skipping build_with_make()')
    return


def clean_up():
    # clean up
    if os.path.isfile('makefile'):
        print('Removing makefile and obj_temp')
        shutil.rmtree(os.path.join('obj_temp'))
        os.remove('makefile')
    if os.path.isfile(target):
        print('Removing ' + target)
        os.remove(target)
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
