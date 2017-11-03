from __future__ import print_function
import os
import sys
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

    # Download the MODFLOW-2005 distribution
    url = "https://water.usgs.gov/ogw/modpath/Modpath_7_1_000.zip"
    download_and_unzip(url)
    dirname = 'Modpath_7_1_000'
    dwpath = os.path.join(dstpth, dirname)
    if os.path.isdir(dwpath):
        shutil.rmtree(dwpath)

    # Name src folders
    srcdir = os.path.join(dirname, 'source')

    # modify source files that prevent compiling with gfortran
    pth = os.path.join(srcdir, 'utl7u1.f')
    if os.path.isfile(pth):
        os.remove(pth)

    fname1 = os.path.join(srcdir, 'ModpathSubCellData.f90')
    f = open(fname1, 'r')
    fname2 = os.path.join(srcdir, 'ModpathSubCellData_mod.f90')
    f2 = open(fname2, 'w')
    for line in f:
        line = line.replace('location.', 'location%')
        f2.write(line)
    f.close()
    f2.close()
    os.remove(fname1)
    os.rename(fname2, fname1)
    
    fname1 = os.path.join(srcdir, 'ModpathCellData.f90')
    f = open(fname1, 'r')
    fname2 = os.path.join(srcdir, 'ModpathCellData_mod.f90')
    f2 = open(fname2, 'w')
    for line in f:
        line = line.replace('dimension(grid%GetCellCount())', 'dimension(:)')
        line = line.replace('dimension(grid%GetReducedConnectionCount())', 'dimension(:)')
        f2.write(line)
    f.close()
    f2.close()
    os.remove(fname1)
    os.rename(fname2, fname1)
    
    fname1 = os.path.join(srcdir, 'MPath7.f90')
    f = open(fname1, 'r')
    fname2 = os.path.join(srcdir, 'MPath7_mod.f90')
    f2 = open(fname2, 'w')
    for line in f:
        line = line.replace("form='binary', access='stream'", "form='unformatted', access='stream'")
        f2.write(line)
    f.close()
    f2.close()
    os.remove(fname1)
    os.rename(fname2, fname1)

    # allow line lengths greater than 132 columns
    fflags='ffree-line-length-512'

    # make modpath 7 in starting directory
    target = os.path.join('..', 'mp7')
    pymake.main(srcdir, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=False, debug=False,
                fflags=fflags)

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

    # change back to the original path
    os.chdir(srcpth)

    # remove temporary directory
    if os.path.isdir(dstpth):
        shutil.rmtree(dstpth)

if __name__ == "__main__":
    make_modpath7()
