from __future__ import print_function
import os
import shutil
import pymake
import flopy

# set up paths
dstpth = os.path.join('temp')
if not os.path.exists(dstpth):
    os.makedirs(dstpth)
mp6pth = os.path.join(dstpth, 'modpath.6_0')
expth = os.path.join(mp6pth, 'test')

exe_name = 'mp6'
srcpth = os.path.join(mp6pth, 'src')
target = os.path.join(dstpth, exe_name)

def compile_code():
    # Remove the existing mfusg directory if it exists
    if os.path.isdir(mp6pth):
        shutil.rmtree(mp6pth)

    # Download the MODPATH 6 distribution
    url = "http://water.usgs.gov/ogw/modpath/modpath.6_0_01.zip"
    pymake.download_and_unzip(url, pth=dstpth)

    fname1 = os.path.join(srcpth, 'MP6Flowdata.for')
    f = open(fname1, 'r')

    fname2 = os.path.join(srcpth, 'MP6Flowdata_mod.for')
    f2 = open(fname2, 'w')
    for line in f:
        line = line.replace('CD.QX2', 'CD%QX2')
        f2.write(line)
    f.close()
    f2.close()
    os.remove(fname1)

    # compile MODPATH 6
    pymake.main(srcpth, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=False, debug=False)
    assert os.path.isfile(target), 'Target does not exist.'


def clean_up():
    # clean up
    print('Removing folder ' + mp6pth)
    shutil.rmtree(mp6pth)
    print('Removing ' + target)
    os.remove(target)
    return

    return


def test_compile():
    # compile MODPATH 6
    compile_code()

def test_clean_up():
    yield clean_up


if __name__ == "__main__":
    compile_code()
    clean_up()
