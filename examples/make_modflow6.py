from __future__ import print_function
import os
import shutil
import pymake
from pymake.download import download_and_unzip


# Download the MODFLOW 6 distribution
def make_mf6():

    # get current directory
    dstpth = os.path.join('temp')
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)
    os.chdir(dstpth)

    # Remove the existing mf6.0.2 directory if it exists
    dirname = 'mf6.0.3'
    if os.path.isdir(dirname):
        shutil.rmtree(dirname)

    url = 'https://water.usgs.gov/ogw/modflow/{0}.zip'.format(dirname)
    download_and_unzip(url)

    # Set src and target
    srcdir = os.path.join(dirname, 'src')
    target = 'mf6'

    pymake.main(srcdir, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=False, debug=False,
                include_subdirs=True)

    assert os.path.isfile(target), 'Target does not exist.'

    # Remove the existing mf6.0.1 directory if it exists
    if os.path.isdir(dirname):
        shutil.rmtree(dirname)

if __name__ == "__main__":
    make_mf6()
