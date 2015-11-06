from __future__ import print_function
import os
import shutil
import pymake


def test_vmodflow2005():

    pth = os.getcwd()
    os.chdir('data')

    dirname = os.path.join('MF2005.1_11u')
    srcpth = os.path.join(dirname, 'src')
    dstpth = os.path.join(dirname, 'dep')

    if not os.path.exists(dstpth):
        os.makedirs(dstpth)

    #--
    pymake.visualize.make_plots(srcpth, dstpth)
    
    os.chdir(pth)


if __name__ == '__main__':
    test_vmodflow2005()
