from __future__ import print_function
import os
import shutil
import pymake
import flopy

# set up paths
dstpth = os.path.join('.', 'temp')
if not os.path.exists(dstpth):
    os.makedirs(dstpth)
mflgrpth = os.path.join(dstpth, 'mflgr.2_0')
expth = os.path.join(mflgrpth, 'test')

exe_name = 'mflgr'
srcpth = os.path.join(mflgrpth, 'src')
target = os.path.join(dstpth, exe_name)

def compile_code():
    # Remove the existing mfusg directory if it exists
    if os.path.isdir(mflgrpth):
        shutil.rmtree(mflgrpth)

    # Download the MODFLOW-LGR distribution
    url = "http://water.usgs.gov/ogw/modflow-lgr/modflow-lgr-v2.0.0/mflgrv2_0_00.zip"
    pymake.download_and_unzip(url, pth=dstpth)

    # compile MODFLOW-LGR
    pymake.main(srcpth, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=False, debug=False)
    assert os.path.isfile(target), 'Target does not exist.'
    return


def clean_up():
    # clean up
    print('Removing folder ' + mflgrpth)
    shutil.rmtree(mflgrpth)
    print('Removing ' + target)
    os.remove(target)
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
