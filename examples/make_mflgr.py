from __future__ import print_function
import os
import shutil
import pymake
from pymake.download import download_and_unzip


def make_mflgr():
    target = 'mflgr'

    # get current directory
    dstpth = os.path.join('temp')
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)

    # compile MODFLOW-lgr
    pymake.build_program(target=target,
                         download_dir=dstpth)

    # Remove the existing mfusg directory if it exists
    if os.path.isdir(dstpth):
        shutil.rmtree(dstpth)


if __name__ == "__main__":
    make_mflgr()
