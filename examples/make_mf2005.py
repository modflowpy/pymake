from __future__ import print_function
import os
import shutil
import pymake
from pymake.download import download_and_unzip


def make_mf2005():

    # get current directory
    dstpth = os.path.join('temp')
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)
    os.chdir(dstpth)

    # Download the MODFLOW-2005 distribution
    url = "https://water.usgs.gov/ogw/modflow/MODFLOW-2005_v1.12.00/MF2005.1_12u.zip"
    download_and_unzip(url)

    # Set dir name
    dirname = 'MF2005.1_12u'
    srcdir = os.path.join(dirname, 'src')

    # make single precision version
    target = 'mf2005'
    pymake.main(srcdir, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=False, debug=False)

    assert os.path.isfile(target), 'Target does not exist.'

    # make double precision version
    target = 'mf2005dbl'
    pymake.main(srcdir, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=True, debug=False)
    
    if sys.platform == 'win32':
        # Based on ifort 12 compilation, 'exe' is appended on the target
        # This necessitates assert expression with different target name
        try:
            # Additional check in case the target does not have 'exe'
            # extension with different compiler 
            assert os.path.isfile(target), 'Target does not exist.'
        except:
            target = target + '.exe'
            
    assert os.path.isfile(target), 'Target does not exist.'

    # Clean up downloaded directory
    if os.path.isdir(dirname):
        shutil.rmtree(dirname)

if __name__ == "__main__":
    make_mf2005()
