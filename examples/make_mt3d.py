from __future__ import print_function
import os
import shutil
import pymake
from pymake.download import download_and_unzip

def make_mt3d():

    # get current directory
    dstpth = os.path.join('temp')
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)
    os.chdir(dstpth)

    # Download the MT3D distribution
    url = "https://hydro.geo.ua.edu/mt3d/mt3dms_530.exe"
    download_and_unzip(url)

    # Set srcdir and remove unneeded files
    srcdir = os.path.join('src', 'true-binary')
    dlist = ['automake.fig', 'mt3dms5b.exe']
    for d in dlist:
        dname = os.path.join(srcdir, d)
        if os.path.isfile(dname):
            print('Removing ', dname)
            os.remove(dname)

    # Replace the getcl command with getarg
    f1 = open(os.path.join(srcdir, 'mt3dms5.for'), 'r')
    f2 = open(os.path.join(srcdir, 'mt3dms5.for.tmp'), 'w')
    for line in f1:
        f2.write(line.replace('CALL GETCL(FLNAME)', 'CALL GETARG(1,FLNAME)'))
    f1.close()
    f2.close()
    os.remove(os.path.join(srcdir, 'mt3dms5.for'))
    shutil.move(os.path.join(srcdir, 'mt3dms5.for.tmp'),
                os.path.join(srcdir, 'mt3dms5.for'))

    # Replace filespec with standard fortran
    l = '''
          CHARACTER*20 ACCESS,FORM,ACTION(2)
          DATA ACCESS/'STREAM'/
          DATA FORM/'UNFORMATTED'/
          DATA (ACTION(I),I=1,2)/'READ','READWRITE'/
    '''
    fn = os.path.join(srcdir, 'FILESPEC.INC')
    f = open(fn, 'w')
    f.write(l)
    f.close()

    target = 'mt3dms'
    pymake.main(srcdir, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=False, debug=False)

    # Clean up unneeded folders
    dlist = ['bin', 'doc', 'examples', 'src', 'utility']
    for d in dlist:
        dname = d
        if os.path.isdir(dname):
            print('Removing ', dname)
            shutil.rmtree(dname)

    # Clean up unneeded files
    for f in ['ReadMe_MT3DMS.pdf', 'upgrade.pdf']:
        print('Removing {}'.format(f))
        os.remove(f)

if __name__ == "__main__":
    make_mt3d()
