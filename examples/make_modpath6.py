from __future__ import print_function
import os
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
    url = "http://water.usgs.gov/ogw/modpath/archive/modpath_v6.0.01/modpath.6_0_01.zip"
    download_and_unzip(url)
    dirname = 'modpath.6_0'
    dwpath = os.path.join(dstpth, dirname)
    if os.path.isdir(dwpath):
        shutil.rmtree(dwpath)

    # Name src folders
    srcdir = os.path.join(dirname, 'src')

    fname1 = os.path.join(srcdir, 'MP6Flowdata.for')
    f = open(fname1, 'r')

    fname2 = os.path.join(srcdir, 'MP6Flowdata_mod.for')
    f2 = open(fname2, 'w')
    for line in f:
        line = line.replace('CD.QX2', 'CD%QX2')
        f2.write(line)
    f.close()
    f2.close()
    os.remove(fname1)

    target = 'mp6'
    pymake.main(srcdir, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=True, debug=False)

    assert os.path.isfile(target), 'Target does not exist.'

#    if os.path.isdir(dirname):
#        shutil.rmtree(dirname)

if __name__ == "__main__":
    make_modpath6()
