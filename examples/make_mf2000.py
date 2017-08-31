from __future__ import print_function
import os
import shutil
import pymake
from pymake.download import download_and_unzip


def make_mf2000():

    # get current directory
    dstpth = os.path.join('temp')
    if os.path.exists(dstpth):
        shutil.rmtree(dstpth)
    os.makedirs(dstpth)
    os.chdir(dstpth)

    # Download the MODFLOW-2005 distribution
    url = "https://water.usgs.gov/nrp/gwsoftware/modflow2000/mf2k1_19_01.tar.gz"
    download_and_unzip(url)

    dirname = 'mf2k.1_19'

    # Set source directory
    srcdir = os.path.join(dirname, 'src')
     
    # Remove six src folders
    dlist = ['beale2k', 'hydprgm', 'mf96to2k', 'mfpto2k', 'resan2k', 'ycint2k']
    for d in dlist:
        dname = os.path.join(srcdir, d)
        if os.path.isdir(dname):
            print('Removing ', dname)
            shutil.rmtree(os.path.join(srcdir, d))

      
    # Move src files and serial src file to src directory
    tpth = os.path.join(srcdir, 'mf2k')
    files = [f for f in os.listdir(tpth) if os.path.isfile(os.path.join(tpth, f))]
    for f in files:
        shutil.move(os.path.join(tpth, f), srcdir)
    tpth = os.path.join(srcdir, 'mf2k', 'serial')
    files = [f for f in os.listdir(tpth) if os.path.isfile(os.path.join(tpth, f))]
    for f in files:
        shutil.move(os.path.join(tpth, f), srcdir)
    
    # Remove mf2k directory in source directory
    tpth = os.path.join(srcdir, 'mf2k')
    shutil.rmtree(tpth)

    # Replace filespec with standard fortran
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

    target = 'mf2000'
    pymake.main(srcdir, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=False, debug=False)

    assert os.path.isfile(target), 'Target does not exist.'

    # Remove MODFLOW-2000 files
    if os.path.isdir(dirname):
        shutil.rmtree(dirname)

if __name__ == "__main__":
    make_mf2000()
