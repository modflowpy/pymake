from __future__ import print_function
import os
import pymake
from pymake.download import download_and_unzip


def make_mfnwt():
    target = 'mfnwt'

    # set download path
    dstpth = os.path.join('temp')

    # compile MODFLOW-NWT
    pymake.build_program(target=target,
                         download_dir=dstpth,
                         download_clean=True)


if __name__ == "__main__":
    make_mfnwt()
