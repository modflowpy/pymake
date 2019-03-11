from __future__ import print_function
import os
import shutil
import pymake


# Download and compile the MODFLOW 6 distribution
def make_mf6():
    target = 'mf6'

    # make a temporary directory for the download
    dstpth = os.path.join('temp')
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)

    # compile MODFLOW 6
    pymake.build_program(target=target,
                         include_subdirs=True,
                         download_dir=dstpth)

    # Remove the temporary download directory if it exists
    if os.path.isdir(dstpth):
        shutil.rmtree(dstpth)

if __name__ == "__main__":
    make_mf6()
