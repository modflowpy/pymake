from __future__ import print_function
import os
import pymake


def make_vs2dt():
    target = 'vs2dt'

    # set download path
    dstpth = os.path.join('temp')

    # compile VS2DT
    pymake.build_program(target=target,
                         replace_function=pymake.update_vs2dtfiles,
                         download_dir=dstpth,
                         download_clean=True)


if __name__ == "__main__":
    make_vs2dt()
