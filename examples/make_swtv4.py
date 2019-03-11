from __future__ import print_function
import os
import shutil
import pymake

def make_swtv4():

    # To compile SEAWAT on mac or linux:
    # 1. The starting source folder should not have the parallel and serial folders
    # 3. The program needs to be compiled in double precision.

    target = 'swt_v4'

    # get current directory
    dstpth = os.path.join('temp')
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)

    # compile seawat
    pymake.build_program(target=target,
                         double=True,
                         download_dir=dstpth,
                         replace_function=pymake.update_seawatfiles,
                         modify_exe_name=False)

    # Clean up downloaded directory
    if os.path.isdir(dstpth):
        shutil.rmtree(dstpth)

    return

if __name__ == "__main__":
    make_swtv4()
