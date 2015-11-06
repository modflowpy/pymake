from __future__ import print_function
import os
import shutil
import pymake
from download import download_and_unzip

# To compile SEAWAT on mac or linux:
# 1. The starting source folder should not have the parallel and serial folders
# 3. The program needs to be compiled in double precision.

# Download the SEAWAT distribution
url = "http://water.usgs.gov/ogw/seawat/swt_v4_00_05.zip"
download_and_unzip(url)

# Remove the parallel and serial folders from the source directory
srcdir = os.path.join('swt_v4_00_05', 'source')
dlist = ['parallel', 'serial']
for d in dlist:
    dname = os.path.join(srcdir, d)
    if os.path.isdir(dname):
        print('Removing ', dname)
        shutil.rmtree(os.path.join(srcdir, d))

# Replace filespec with standard fortran
l = '''
      CHARACTER*20 ACCESS,FORM,ACTION(2)
      DATA ACCESS/'STREAM'/
      DATA FORM/'UNFORMATTED'/
      DATA (ACTION(I),I=1,2)/'READ','READWRITE'/
'''
fn = os.path.join(srcdir, 'filespec.inc')
f = open(fn, 'w')
f.write(l)
f.close()

target = 'swtv4'
pymake.main(srcdir, target, 'gfortran', makeclean=True, expedite=False,
            dryrun=False, double=True, debug=False)
