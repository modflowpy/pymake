from __future__ import print_function
import os
import sys
import shutil
import pymake
from pymake.download import download_and_unzip

def make_mt3dusgs():

    # get current directory
    dstpth = os.path.join('temp')
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)
    os.chdir(dstpth)

    # Remove the existing MT3D-USGS directory if it exists
    dirname = 'mt3d-usgs_Distribution'
    if os.path.isdir(dirname):
        shutil.rmtree(dirname)

    # Download the MT3D-USGS distribution
    url = "https://water.usgs.gov/ogw/mt3d-usgs/mt3d-usgs_1.0.zip"
    download_and_unzip(url)

    # Set srcdir and target
    srcdir = os.path.join(dirname, 'src')
    target = 'mt3dusgs'

    # Replace openspec with standard fortran
    l = '''
          CHARACTER*20 ACCESS,FORM,ACTION(2)
          DATA ACCESS/'STREAM'/
          DATA FORM/'UNFORMATTED'/
          DATA (ACTION(I),I=1,2)/'READ','READWRITE'/
    '''
    fn = os.path.join(srcdir, 'openspec.inc')
    f = open(fn, 'w')
    f.write(l)
    f.close()

    pymake.main(srcdir, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=False, debug=False)

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

    # Remove the existing MT3D-USGS directory if it exists
    if os.path.isdir(dirname):
        shutil.rmtree(dirname)

if __name__ == "__main__":
    make_mt3dusgs()
