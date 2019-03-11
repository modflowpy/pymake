from __future__ import print_function
import os
import shutil
import pymake


def make_mf2005():
    target = 'mf2005'

    # get current directory
    dstpth = os.path.join('temp')
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)

    # make single precision version of MODFLOW-2005
    pymake.build_program(target=target,
                         download_dir=dstpth)

    # make double precision version of MODFLOW-2005
    pymake.build_program(target=target, double=True,
                         download_dir=dstpth, download=False)

    # Clean up downloaded directory
    if os.path.isdir(dstpth):
        shutil.rmtree(dstpth)

if __name__ == "__main__":
    make_mf2005()
