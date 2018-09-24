from __future__ import print_function
import os
import shutil
import pymake
from pymake.download import download_and_unzip


def make_modpath7():

    # get current directory
    srcpth = os.getcwd()
    dstpth = os.path.join('temp')
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)
    os.chdir(dstpth)

    # Download the MODPATH 7 distribution
    url = "https://water.usgs.gov/ogw/modpath/modpath_7_2_001.zip"
    download_and_unzip(url)
    dirname = 'Modpath_7_2_001'
    dwpath = os.path.join(dstpth, dirname)
    if os.path.isdir(dwpath):
        shutil.rmtree(dwpath)

    # Name src folders
    srcdir = os.path.join(dirname, 'source')

    # allow line lengths greater than 132 columns
    fflags='ffree-line-length-512'

    # make modpath 7 in starting directory
    target = os.path.join('.', 'mp7')
    pymake.main(srcdir, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=False, debug=False,
                fflags=fflags)

    assert os.path.isfile(target), 'Target does not exist.'

    # change back to the original path
    os.chdir(srcpth)

    # remove temporary directory
    if os.path.isdir(dwpath):
        shutil.rmtree(dwpath)

if __name__ == "__main__":
    make_modpath7()
