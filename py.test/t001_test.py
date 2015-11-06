from __future__ import print_function
import os
import shutil
import pymake


def test_modflow2005():

    pth = os.getcwd()
    os.chdir('data')

    # Download the MODFLOW-2005 distribution
    url = 'http://water.usgs.gov/ogw/modflow/MODFLOW-2005_v1.11.00/mf2005v1_11_00_unix.zip'
    pymake.download_and_unzip(url)

    # Rename Unix to a more reasonable name
    dirname = os.path.join('MF2005.1_11u')
    if os.path.isdir(dirname):
        shutil.rmtree(dirname)
    os.rename(os.path.join('Unix'), os.path.join('MF2005.1_11u'))

    srcdir = os.path.join(dirname, 'src')
    target = 'mf2005dbl'

    # compile modflow
    pymake.main(srcdir, target, 'gfortran', makeclean=True, expedite=False,
                dryrun=False, double=True, debug=False, include_subdirs=False)

    os.chdir(pth)


if __name__ == '__main__':
    test_modflow2005()
