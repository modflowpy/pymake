from __future__ import print_function
import os
import shutil
import pymake
from pymake.download import download_and_unzip

def make_swtv4():

    # To compile SEAWAT on mac or linux:
    # 1. The starting source folder should not have the parallel and serial folders
    # 3. The program needs to be compiled in double precision.

    # get current directory
    dstpth = os.path.join('temp')
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)
    os.chdir(dstpth)

    # Remove the existing directory if it exists
    dirname = 'swt_v4_00_05'
    if os.path.isdir(dirname):
        shutil.rmtree(dirname)

    # Download the SEAWAT distribution
    url = "https://water.usgs.gov/ogw/seawat/{0}.zip".format(dirname)
    download_and_unzip(url)

    # Remove the parallel and serial folders from the source directory
    srcdir = os.path.join(dirname, 'source')
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
    try:
        os.remove(os.path.join(srcdir, 'FILESPEC.INC'))
    except:
        pass
    fn = os.path.join(srcdir, 'filespec.inc')
    f = open(fn, 'w')
    f.write(l)
    f.close()
    
    # rename all source files to lower case so compilation doesn't
    # bomb on case-sensitive operating systems
    srcfiles = os.listdir(srcdir)
    for filename in srcfiles:
        src = os.path.join(srcdir, filename)
        dst = os.path.join(srcdir, filename.lower())
        os.rename(src, dst)

    # make target
    target = 'swtv4'
    pymake.main(srcdir, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=True, debug=False)

    assert os.path.isfile(target), 'Target does not exist.'

    # Remove the existing directory if it exists
    #if os.path.isdir(dirname):
    #    shutil.rmtree(dirname)

    return

if __name__ == "__main__":
    make_swtv4()
