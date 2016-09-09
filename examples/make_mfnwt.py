from __future__ import print_function
import os
import shutil
import pymake
from pymake.download import download_and_unzip

def make_mfnwt():

    # Note, this script does not work yet due to some non-standard Fortran
    # in one or more of the source files.

    # get current directory
    dstpth = os.path.join('temp')
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)
    os.chdir(dstpth)

    # Remove the existing directory if it exists
    dirname = 'MODFLOW-NWT_1.1.1'
    if os.path.isdir(dirname):
        shutil.rmtree(dirname)

    # Download the MODFLOW-NWT distribution
    url = "http://water.usgs.gov/ogw/modflow-nwt/MODFLOW-NWT-v1.1.1/MODFLOW-NWT_1.1.1.zip"
    download_and_unzip(url)

    # Remove the parallel and serial folders from the source directory
    srcdir = os.path.join('MODFLOW-NWT_1.1.1', 'src')
    target = 'mfnwt'

    pymake.main(srcdir, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=False, debug=False)

    assert os.path.isfile(target), 'Target does not exist.'

    # Clean up
    dirname = 'MODFLOW-NWT_1.1.1'
    if os.path.isdir(dirname):
        shutil.rmtree(dirname)

if __name__ == "__main__":
    make_mfnwt()
