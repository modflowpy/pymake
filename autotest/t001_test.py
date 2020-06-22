from __future__ import print_function
import os
import sys
import shutil

import pymake
from pymake.autotest import get_namefiles

import flopy

retain = False
key_release = 'mf2005'
key_previous = 'mf2005.1.11'
pd_release = pymake.usgs_program_data.get_target(key=key_release)
pd_previous = pymake.usgs_program_data.get_target(key=key_previous)

testdir = 'temp'
testdir_release = os.path.join(testdir, pd_release.dirname)
target_release = os.path.join(testdir, key_release)

testdir_previous = os.path.join(testdir, pd_previous.dirname)
target_previous = os.path.join(testdir, key_previous)

if sys.platform.lower() == 'win32':
    target_release += '.exe'
    target_previous += '.exe'

exdir = 'test-run'
testpaths = [os.path.join(testdir, pd_release.dirname, exdir)]
exclude = ('MNW2-Fig28', 'swi2ex4sww', 'testsfr2_tab', 'UZFtest2')

def mf2005_namefiles():
    if os.path.isdir(testpaths[0]):
        namefiles = get_namefiles(testpaths[0], exclude=exclude)
    else:
        namefiles = [None]
    return namefiles


def run_mf2005(namefile, regression=True):
    """
    Run the simulation.

    """
    if namefile is not None:
        # Set root as the directory name where namefile is located
        testname = pymake.get_sim_name(namefile, rootpth=testpaths[0])[0]

        # Set nam as namefile name without path
        nam = os.path.basename(namefile)

        # Setup
        testpth = os.path.join(testdir, testname)
        pymake.setup(namefile, testpth)

        # run test models
        exe_name = os.path.abspath(target_release)
        msg = 'running model...{}'.format(testname) + \
              ' using {}'.format(exe_name)
        print(msg)
        if os.path.exists(exe_name):
            success, buff = flopy.run_model(exe_name, nam, model_ws=testpth,
                                            silent=True)
        else:
            success = False

        assert success, 'base model {} '.format(nam) + 'did not run.'

        # If it is a regression run, then setup and run the model with the
        # release target and the reference target
        success_reg = True
        if regression:
            testname_reg = os.path.basename(target_previous)
            testpth_reg = os.path.join(testpth, testname_reg)
            pymake.setup(namefile, testpth_reg)
            # exe_name = os.path.abspath(target_previous)
            msg = 'running regression model...{}'.format(testname_reg) + \
                  ' using {}'.format(exe_name)
            print(msg)

            if os.path.exists(exe_name):
                success_reg, buff = flopy.run_model(exe_name, nam,
                                                    model_ws=testpth_reg,
                                                    silent=False)
            else:
                success_reg = False

            assert success_reg, 'regression model {} '.format(nam) + \
                                'did not run.'

        # compare results
        if success and success_reg:
            fpth = os.path.split(os.path.join(testpth, nam))[0]
            outfile1 = os.path.join(fpth, 'bud.cmp')
            fpth = os.path.split(os.path.join(testpth, nam))[0]
            outfile2 = os.path.join(fpth, 'hds.cmp')
            success_reg = pymake.compare(os.path.join(testpth, nam),
                                         os.path.join(testpth_reg, nam),
                                         precision='single',
                                         max_cumpd=0.01, max_incpd=0.01,
                                         htol=0.001,
                                         outfile1=outfile1, outfile2=outfile2)
        # Clean things up
        if success_reg:
            if not retain:
                pymake.teardown(testpth)
        else:
            success = False
            errmsg = 'could not run...{}'.format(os.path.basename(nam))
    else:
        success = False
        errmsg = '{} does not exist'.format(target_release)

    assert success, errmsg

    return
#
#
# def test_compile_prev():
#     # Compile reference version of the program from the source.
#
#     # Remove the existing distribution directory if it exists
#     if os.path.isdir(testdir_previous):
#         print('Removing folder ' + testdir_previous)
#         shutil.rmtree(testdir_previous)
#
#     pymake.build_program(target=key_previous, fflags='-O3', cflags='-O3',
#                          download_dir=testdir,
#                          exe_name=target_previous)
#
#     return


def test_compile_ref():
    # Compile reference version of the program from the source.

    # Remove the existing distribution directory if it exists
    if os.path.isdir(testdir_release):
        print('Removing folder ' + testdir_release)
        shutil.rmtree(testdir_release)

    pymake.build_program(target=key_release,
                         fc='gfortran', cc='gcc',
                         fflags='-O3 -fbacktrace', cflags='-O3',
                         download_dir=testdir,
                         exe_name=target_release)

    return


def test_mf2005():
    for namefile in mf2005_namefiles():
        yield run_mf2005, namefile
    return


def test_cleanup():
    ext = ''
    if sys.platform == 'win32':
        ext = '.exe'

    # clean up targets
    ttarget = target_previous + ext
    if os.path.isfile(ttarget):
        print('Removing ' + target_previous)
        os.remove(ttarget)

    ttarget = target_release + ext
    if os.path.isfile(ttarget):
        print('Removing ' + target_release)
        os.remove(ttarget)

    # remove release source files if target was built
    if os.path.isdir(testdir_release):
        print('Removing folder ' + testdir_release)
        shutil.rmtree(testdir_release)

    # remove previous release source files if target was built
    if os.path.isdir(testdir_previous):
        print('Removing folder ' + testdir_previous)
        shutil.rmtree(testdir_previous)

    return


if __name__ == '__main__':
    test_compile_ref()
    # test_compile_prev()

    for namefile in mf2005_namefiles():
        run_mf2005(namefile)

    test_mf2005()
    test_cleanup()
