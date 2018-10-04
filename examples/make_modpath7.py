from __future__ import print_function
import os
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

    # Download the MODPATH 7 distribution
    url = "https://water.usgs.gov/ogw/modpath/modpath_7_2_001.zip"
    download_and_unzip(url)
    dirname = 'modpath_7_2_001'
    dwpath = os.path.join(dstpth, dirname)
    if os.path.isdir(dwpath):
        shutil.rmtree(dwpath)

    # Name src folders
    srcdir = os.path.join(dirname, 'source')

    # modify files to address issues related to specific compilers and/or bugs
    update_mp7files(srcdir)

    # allow line lengths greater than 132 columns
    fflags = 'ffree-line-length-512'

    # make modpath 7 in starting directory
    target = os.path.join('.', 'mp7')
    pymake.main(srcdir, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=False, debug=False,
                fflags=fflags)

    assert os.path.isfile(target), 'Target does not exist.'

    # change back to the original path
    os.chdir(srcpth)

    # remove temporary directory
    if os.path.isdir(dwpath):
        shutil.rmtree(dwpath)


def update_mp7files(srcdir):
    fpth = os.path.join(srcdir, 'StartingLocationReader.f90')
    with open(fpth) as f:
        lines = f.readlines()
    f = open(fpth, 'w')
    for line in lines:
        if 'pGroup%Particles(n)%InitialFace = 0' in line:
            continue
        f.write(line)
    f.close()


if __name__ == "__main__":
    make_modpath7()
