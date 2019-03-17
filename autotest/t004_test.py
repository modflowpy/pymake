from __future__ import print_function
import os
import shutil

import pymake
import flopy

# define program data
target = 'mp6'
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join('temp')
if not os.path.exists(dstpth):
    os.makedirs(dstpth)

mp6pth = os.path.join(dstpth, prog_dict.dirname)
expth = os.path.join(mp6pth, 'example-run')

exe_name = 'mp6'
srcpth = os.path.join(mp6pth, prog_dict.srcdir)
epth = os.path.abspath(os.path.join(dstpth, target))


# Download and compile the MODPATH 6 distribution
def compile_code():
    # Remove the existing MODPATH 6 directory if it exists
    if os.path.isdir(mp6pth):
        shutil.rmtree(mp6pth)

    # download and compile MODPATH 6
    replace_function = pymake.build_replace(target)
    pymake.build_program(target=target,
                         download_dir=dstpth,
                         exe_dir=dstpth,
                         replace_function=replace_function)


def get_simfiles():
    simfiles = [f for f in os.listdir(expth) if f.endswith('.mpsim')]
    return simfiles


def run_modpath6(fn):
    # rename a few files for linux
    replace_files = ['example-6', 'example-7', 'example-8']
    for rf in replace_files:
        if rf in fn.lower():
            fname1 = os.path.join(expth, '{}.locations'.format(rf))
            fname2 = os.path.join(expth, '{}_mod.locations'.format(rf))
            print('copy {} to {}'.format(os.path.basename(fname1),
                                         os.path.basename(fname2)))
            shutil.copy(fname1, fname2)
            print('deleting {}'.format(os.path.basename(fname1)))
            os.remove(fname1)
            fname1 = os.path.join(expth, '{}.locations'.format(rf.upper()))
            print('renmae {} to {}'.format(os.path.basename(fname2),
                                           os.path.basename(fname1)))
            os.rename(fname2, fname1)

    # run the model
    print('running model...{}'.format(fn))
    success, buff = flopy.run_model(epth, fn, model_ws=expth, silent=False)
    assert success, 'could not run...{}'.format(os.path.basename(fn))
    return


def clean_up():
    # clean up download directory
    print('Removing folder ' + mp6pth)
    shutil.rmtree(mp6pth)

    # clean up executable
    print('Removing ' + target)
    os.remove(epth)
    return


def test_compile():
    # compile MODPATH 6
    compile_code()


def test_modpath6():
    simfiles = get_simfiles()
    for fn in simfiles:
        yield run_modpath6, fn


def test_clean_up():
    yield clean_up


if __name__ == "__main__":
    compile_code()
    simfiles = get_simfiles()
    for fn in simfiles:
        run_modpath6(fn)
    clean_up()
