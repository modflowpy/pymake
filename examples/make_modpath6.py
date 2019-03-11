from __future__ import print_function
import os
import shutil

import pymake


def make_modpath6():
    target = 'mp6'

    # get current directory
    dstpth = os.path.join('temp')
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)

    # compile MODPATH 6
    pymake.build_program(target=target,
                         download_dir=dstpth,
                         replace_function=pymake.update_mp6files)

    # Remove the existing mfusg directory if it exists
    if os.path.isdir(dstpth):
        shutil.rmtree(dstpth)

if __name__ == "__main__":
    make_modpath6()
