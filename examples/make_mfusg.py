from __future__ import print_function
import os
import shutil
import pymake
from pymake.download import download_and_unzip


# Download the MODFLOW-USG distribution
def make_mfusg():

    # get current directory
    dstpth = os.path.join('temp')
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)
    os.chdir(dstpth)

    # Remove the existing mfusg.1_3 directory if it exists
    dirname = 'mfusg.1_4'
    if os.path.isdir(dirname):
        shutil.rmtree(dirname)

    url = 'https://water.usgs.gov/ogw/mfusg/{0}.zip'.format(dirname)
    download_and_unzip(url)

    # Set src and target
    srcdir = os.path.join(dirname, 'src')
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

    # Remove the existing mfusg directory if it exists
    if os.path.isdir(dirname):
        shutil.rmtree(dirname)

if __name__ == "__main__":
    make_mfusg()
