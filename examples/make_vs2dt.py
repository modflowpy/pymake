from __future__ import print_function
import os
import shutil
import pymake
from pymake.download import download_and_unzip


def update_vs2dtfiles(srcdir):

    # move the main source into the source directory
    f1 = os.path.join(srcdir, '..', 'vs2dt3_3.f')
    f1 = os.path.abspath(f1)
    assert os.path.isfile(f1)
    f2 = os.path.join(srcdir, 'vs2dt3_3.f')
    f2 = os.path.abspath(f2)
    shutil.move(f1, f2)
    assert os.path.isfile(f2)

    f1 = open(os.path.join(srcdir, 'vs2dt3_3.f'), 'r')
    f2 = open(os.path.join(srcdir, 'vs2dt3_3.f.tmp'), 'w')
    for line in f1:
        srctxt = "     `POSITION='REWIND')"
        rpctxt = "     `POSITION='REWIND',ACCESS='STREAM')"
        f2.write(line.replace(srctxt, rpctxt))
    f1.close()
    f2.close()
    os.remove(os.path.join(srcdir, 'vs2dt3_3.f'))
    shutil.move(os.path.join(srcdir, 'vs2dt3_3.f.tmp'),
                os.path.join(srcdir, 'vs2dt3_3.f'))

    return


def make_vs2dt():

    # get current directory
    dstpth = os.path.join('temp')
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)
    os.chdir(dstpth)

    # Download the distribution
    dirname = 'vs2dt3_3'
    url = 'https://water.usgs.gov/water-resources/software/VS2DI/{}.zip'.format(dirname)
    download_and_unzip(url, verify=False, timeout=15)

    # Set srcdir and remove unneeded files
    srcdir = os.path.join(dirname, 'include')

    # change to access='stream'
    update_vs2dtfiles(srcdir)

    target = 'vs2dt'
    pymake.main(srcdir, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=False, debug=False)

    # Clean up unneeded folders
    dlist = []
    for d in dlist:
        dname = d
        if os.path.isdir(dname):
            print('Removing ', dname)
            shutil.rmtree(dname)

    # Clean up unneeded files
    for f in []:
        print('Removing {}'.format(f))
        os.remove(f)

if __name__ == "__main__":
    make_vs2dt()
