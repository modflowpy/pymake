from __future__ import print_function
import os
import shutil
import pymake


def test_mfusg():

    # get current directory
    pth = os.getcwd()
    dstpth = os.path.join('temp')
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)
    os.chdir(dstpth)

    # Remove the existing mfusg.1_2 directory if it exists
    dirname = 'mfusg.1_2'
    if os.path.isdir(dirname):
        shutil.rmtree(dirname)

    url = 'http://water.usgs.gov/ogw/mfusg/mfusg.1_2_00.zip'
    pymake.download_and_unzip(url)

    # Set src and target
    srcdir = os.path.join('mfusg.1_2', 'src')
    target = 'mfusg'

    # Remove extraneous source directories
    dlist = ['zonebudusg', 'serial']
    for d in dlist:
        dname = os.path.join(srcdir, d)
        if os.path.isdir(dname):
            print('Removing ', dname)
            shutil.rmtree(os.path.join(srcdir, d))

    pymake.main(srcdir, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=False, debug=False)

    assert os.path.isfile(target), 'Target does not exist.'

    # Remove the existing mfusg.1_2 directory if it exists
    dirname = 'mfusg.1_2'
    if os.path.isdir(dirname):
        shutil.rmtree(dirname)

    # change back to the starting directory
    os.chdir(pth)

if __name__ == "__main__":
    test_mfusg()
