from __future__ import print_function
import os
import sys
import shutil
import pymake
from pymake.download import download_and_unzip


def make_modpath6():

    # get current directory
    dstpth = os.path.join('temp')
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)
    os.chdir(dstpth)

    # Download the MODFLOW-2005 distribution
    url = "https://water.usgs.gov/ogw/modpath/archive/modpath_v6.0.01/modpath.6_0_01.zip"
    download_and_unzip(url)
    dirname = 'modpath.6_0'
    dwpath = os.path.join(dstpth, dirname)
    if os.path.isdir(dwpath):
        shutil.rmtree(dwpath)

    # Name src folders
    srcdir = os.path.join(dirname, 'src')

    # start of edit a few files so it can compile with gfortran
    # file 1
    fname1 = os.path.join(srcdir, 'MP6Flowdata.for')
    f = open(fname1, 'r')

    bigline = 'CB%BALANCE = ABS(100.0*CB%QRESIDUAL/CB%QAVE)'
    newline = '      IF (ABS(CB%QAVE) > 0.) THEN\n' + \
              '        CB%BALANCE = ABS(100.0*CB%QRESIDUAL/CB%QAVE)\n' + \
              '      ELSE\n' + \
              '        CB%BALANCE = 0.\n' + \
              '      END IF\n'

    fname2 = os.path.join(srcdir, 'MP6Flowdata_mod.for')
    f2 = open(fname2, 'w')
    for line in f:
        line = line.replace('CD.QX2', 'CD%QX2')
        if bigline in line:
            line = newline
        f2.write(line)
    f.close()
    f2.close()
    os.remove(fname1)
        
    # file 2
    fname1 = os.path.join(srcdir, 'MP6MPBAS1.for')
    f = open(fname1, 'r')

    fname2 = os.path.join(srcdir, 'MP6MPBAS1_mod.for')
    f2 = open(fname2, 'w')
    for line in f:
        line = line.replace('MPBASDAT(IGRID)%NCPPL=NCPPL', 
                            'MPBASDAT(IGRID)%NCPPL=>NCPPL')
        f2.write(line)
    f.close()
    f2.close()
    os.remove(fname1)
    # end of edit a few files so it can compile with gfortran

    target = 'mp6'
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

    # if os.path.isdir(dirname):
    #     shutil.rmtree(dirname)

if __name__ == "__main__":
    make_modpath6()
