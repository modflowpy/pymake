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
epth = os.path.join(dstpth, target)


def get_example_dirs():
    if os.path.isdir(expth):
        exdirs = sorted([o for o in os.listdir(expth)
                         if os.path.isdir(os.path.join(expth, o))])
    else:
        exdirs = [None]
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
                         replace_function=replace_function,
                         exe_dir=dstpth,
                         dryrun=False,
                         makefile=True)


def build_with_makefile():
    if os.path.isfile('makefile'):

        tepth = epth
        if sys.platform.lower() == 'win32':
            tepth += '.exe'

        # remove existing target
        if os.path.isfile(tepth):
            print('Removing ' + target)
            os.remove(tepth)

        print('Removing temporary build directories')
        dirs_temp = [os.path.join('src_temp'),
                     os.path.join('obj_temp'),
                     os.path.join('mod_temp')]
        for d in dirs_temp:
            if os.path.isdir(d):
                shutil.rmtree(d)

        # build MODFLOW 6 with makefile
        print('build {} with makefile'.format(target))
        os.system('make')

        # verify that MODFLOW 6 was made
        errmsg = '{} created by makefile does not exist.'.format(target)
        success = os.path.isfile(tepth)
    else:
        errmsg = 'makefile does not exist...skipping build_with_make()'
        success = False

    assert success, errmsg

    return


def clean_up():
    # clean up makefile
    print('Removing makefile')
    files = ['makefile', 'makedefaults']
    for fpth in files:
        if os.path.isfile(fpth):
            os.remove(fpth)

    print('Removing temporary build directories')
    dirs_temp = [os.path.join('obj_temp'),
                 os.path.join('mod_temp')]
    for d in dirs_temp:
        if os.path.isdir(d):
            shutil.rmtree(d)

    # clean up
    print('Removing folder ' + mf6pth)
    if os.path.isdir(mf6pth):
        shutil.rmtree(mf6pth)

    tepth = epth
    if sys.platform == 'win32':
        tepth += '.exe'

    if os.path.isfile(tepth):
        print('Removing ' + target)
        os.remove(tepth)
    return


def run_mf6(ws):
    exe_name = os.path.abspath(epth)
    if os.path.exists(exe_name):
        print('running...{}'.format(ws))
        # setup
        src = os.path.join(expth, ws)
        dst = os.path.join(dstpth, ws)
        pymake.setup_mf6(src, dst)

        # run test models
        print('running model...{}'.format(os.path.basename(ws)))
        success, buff = flopy.run_model(exe_name, None,
                                        model_ws=dst, silent=False)
        if not success:
            errmsg = 'could not run {}'.format(os.path.basename(ws))
    else:
        success = False
        errmsg = 'could not run {}'.format(exe_name)

    if success:
        pymake.teardown(dst)

    assert success, errmsg

    return


def test_compile():
    # compile MODFLOW-USG
    compile_code()


def test_mf6():
    # get name files and simulation name
    example_dirs = get_example_dirs()
    # run models
    for ws in example_dirs:
        yield run_mf6, ws


def test_makefile():
    build_with_makefile()


def test_clean_up():
    yield clean_up


if __name__ == "__main__":
    # compile MODFLOW 6
    compile_code()

    # get name files and simulation name
    example_dirs = get_example_dirs()

    # run models
    for ws in example_dirs:
        run_mf6(ws)

    # build modflow 6 with a pymake generated makefile
    build_with_makefile()

    # clean up
    clean_up()
