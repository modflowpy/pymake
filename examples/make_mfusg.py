from __future__ import print_function
import os
import shutil
import pymake


# Download and compile the MODFLOW-USG distribution
def make_mfusg():
    target = 'mfusg'

    # get current directory
    dstpth = os.path.join('temp')
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)

    # compile MODFLOW-USG
    pymake.build_program(target=target,
                         download_dir=dstpth)

    # Remove the existing mfusg directory if it exists
    if os.path.isdir(dstpth):
        shutil.rmtree(dstpth)

if __name__ == "__main__":
    make_mfusg()
