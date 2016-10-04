from __future__ import print_function
import os
import shutil
import pymake
from pymake.download import download_and_unzip

def make_mfnwt():

    # get current directory
    dstpth = os.path.join('temp')
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)
    os.chdir(dstpth)

    # Remove the existing directory if it exists
    dirname = 'MODFLOW-NWT_1.1.2'
    if os.path.isdir(dirname):
        shutil.rmtree(dirname)

    # Download the MODFLOW-NWT distribution
    url = "http://water.usgs.gov/ogw/modflow-nwt/{0}.zip".format(dirname)
    download_and_unzip(url)

    # Remove the parallel and serial folders from the source directory
    srcdir = os.path.join(dirname, 'src')
    target = 'mfnwt'

    pymake.main(srcdir, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=False, debug=False)

    assert os.path.isfile(target), 'Target does not exist.'

    # Clean up
    if os.path.isdir(dirname):
        shutil.rmtree(dirname)

if __name__ == "__main__":
    make_mfnwt()
