from __future__ import print_function
import os
import sys
import shutil
import pymake
import flopy

# define program data
target = 'mf6'
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join('temp')
if not os.path.exists(dstpth):
    os.makedirs(dstpth)

mf6ver = prog_dict.version
mf6pth = os.path.join(dstpth, prog_dict.dirname)
expth = os.path.join(mf6pth, 'examples')


def get_example_dirs():
    exdirs = [o for o in os.listdir(expth)
              if os.path.isdir(os.path.join(expth, o))]
    return exdirs


def compile_code():
    # Remove the existing mf6 directory if it exists
    if os.path.isdir(mf6pth):
        shutil.rmtree(mf6pth)

    # compile MODFLOW 6
    pymake.usgs_program_data().list_targets(current=True)
    replace_function = pymake.build_replace(target)
    pymake.build_program(target=target,
                         include_subdirs=True,
                         download_dir=dstpth,
                         replace_function=replace_function)


def clean_up():
    # clean up
    print('Removing folder ' + mf6pth)
    shutil.rmtree(mf6pth)

    ext = ''
    if sys.platform == 'win32':
        ext = '.exe'

    print('Removing ' + target)
    os.remove(target + ext)
    return


def run_mf6(d):
    print('running...{}'.format(d))
    # setup
    epth = os.path.join(expth, d)
    testpth = os.path.join(dstpth, d)
    pymake.setup_mf6(epth, testpth)

    # run test models
    print('running model...{}'.format(os.path.basename(d)))
    epth = os.path.abspath(target)
    success, buff = flopy.run_model(epth, None,
                                    model_ws=testpth, silent=False)
    if success:
        pymake.teardown(testpth)
    assert success is True

    return


def test_compile():
    # compile MODFLOW-USG
    compile_code()


def test_mf6():
    # get name files and simulation name
    example_dirs = get_example_dirs()
    # run models
    for d in example_dirs:
        yield run_mf6, d


def test_clean_up():
    yield clean_up


if __name__ == "__main__":
    # compile MODFLOW 6
    compile_code()
    # get name files and simulation name
    example_dirs = get_example_dirs()
    # run models
    for d in example_dirs:
        run_mf6(d)
    # clean up
    clean_up()
