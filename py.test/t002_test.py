from __future__ import print_function
import os
import shutil
import pymake


def test_vmodflow2005():

    # get current directory
    pth = os.getcwd()
    # working directory
    dstpth = os.path.join('temp')
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)
    # change to temp subdirectory
    os.chdir(dstpth)

    dirname = os.path.join('MF2005.1_11u')
    srcpth = os.path.join(dirname, 'src')

    # create the directory for the output if it doesn't exist
    dstpth = os.path.join(dirname, 'dep')
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)

    #--
    pymake.visualize.make_plots(srcpth, dstpth)
    
    os.chdir(pth)


if __name__ == '__main__':
    test_vmodflow2005()
