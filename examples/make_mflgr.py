from __future__ import print_function
import os
import sys
import shutil
import pymake
from pymake.download import download_and_unzip


def make_mflgr():

    # get current directory
    dstpth = os.path.join('temp')
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)
    os.chdir(dstpth)

    # Download the MODFLOW-LGR distribution
    url = "https://water.usgs.gov/ogw/modflow-lgr/modflow-lgr-v2.0.0/mflgrv2_0_00.zip"
    download_and_unzip(url)

    dirname = 'mflgr.2_0'
    srcdir = os.path.join(dirname, 'src')
    target = 'mflgrdbl'

    print('Present working directory: ', os.getcwd())
    # pymake.main(srcdir, target, 'ifort', 'gcc', makeclean=True,
    #            expedite=False, dryrun=False, double=True, debug=False)
    pymake.main(srcdir, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=True, debug=False)
    
    if sys.platform == 'win32':
        # 'exe' is appended to the target name upon compilation
        # 'exe' is not appended if target already has extension part
        try:
            # Additional check in case the target does not have 'exe'
            # extension with different compiler 
            assert os.path.isfile(target), 'Target does not exist.'
        except:
            if not '.' in target:
                target = target + '.exe'
            
    assert os.path.isfile(target), 'Target does not exist.'

if __name__ == "__main__":
    make_mflgr()
