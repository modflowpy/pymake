from __future__ import print_function
import pymake


# Download and compile the MODFLOW 6 distribution
def make_mf6():

    # compile MODFLOW 6
    pymake.build_program(target='mf6',
                         include_subdirs=True,
                         download_dir='temp',
                         download_clean=True)


if __name__ == "__main__":
    make_mf6()
