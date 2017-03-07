from __future__ import print_function
import os
import sys
import shutil
import pymake
from pymake.autotest import get_namefiles, compare_budget, compare_heads
import flopy
import config001 as config


def run_mf2005(namefile, regression=True):
    """
    Run the simulation.

    """

    # Set root as the directory name where namefile is located
    testname = pymake.get_sim_name(namefile, rootpth=config.testpaths[0])[0]

    # Set nam as namefile name without path
    nam = os.path.basename(namefile)

    # Setup
    testpth = os.path.join(config.testdir, testname)
    pymake.setup(namefile, testpth)

    # run test models
    print('running model...{}'.format(testname))
    exe_name = os.path.abspath(config.target_release)
    success, buff = flopy.run_model(exe_name, nam, model_ws=testpth,
                                    silent=True)

    assert success, 'base model {} '.format(nam) + 'did not run.'

    # If it is a regression run, then setup and run the model with the
    # release target and the reference target
    success_reg = True
    if regression:
        testname_reg = os.path.basename(config.target_previous)
        testpth_reg = os.path.join(testpth, testname_reg)
        pymake.setup(namefile, testpth_reg)
        print('running regression model...{}'.format(testname_reg))
        exe_name = os.path.abspath(config.target_previous)
        success_reg, buff = flopy.run_model(exe_name, nam,
                                            model_ws=testpth_reg,
                                            silent=False)

        assert success_reg, 'regression model {} '.format(nam) + 'did not run.'

        # compare results
        outfile1 = os.path.join(os.path.split(os.path.join(testpth, nam))[0], 'bud.cmp')
        outfile2 = os.path.join(os.path.split(os.path.join(testpth, nam))[0], 'hds.cmp')
        success_reg = pymake.compare(os.path.join(testpth, nam),
                                     os.path.join(testpth_reg, nam),
                                     precision='single',
                                     max_cumpd=0.01, max_incpd=0.01, htol=0.001,
                                     outfile1=outfile1, outfile2=outfile2)

    # Clean things up
    if not config.retain:
        pymake.teardown(testpth)

    return


def test_compile_prev():
    # Compile reference version of the program from the source.

    # Remove the existing distribution directory if it exists
    dir_previous = config.dir_previous
    if os.path.isdir(dir_previous):
        print('Removing folder ' + dir_previous)
        shutil.rmtree(dir_previous)

    # Setup variables
    url = config.url_previous
    srcdir = config.srcdir_previous
    target = config.target_previous

    # Download the MODFLOW-2005 distribution
    pymake.download_and_unzip(url, pth=config.testdir)

    # compile
    pymake.main(srcdir, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=False, debug=False,
                include_subdirs=False)

    assert os.path.isfile(target), 'Target {} does not exist.'.format(target)

    return


def test_compile_ref():
    # Compile reference version of the program from the source.

    # Remove the existing distribution directory if it exists
    dir_release = config.dir_release
    if os.path.isdir(dir_release):
        print('Removing folder ' + dir_release)
        shutil.rmtree(dir_release)

    # Setup variables
    url = config.url_release
    srcdir = config.srcdir_release
    target = config.target_release

    # Download the MODFLOW-USG distribution
    pymake.download_and_unzip(url, pth=config.testdir)

    # compile
    pymake.main(srcdir, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=False, debug=False,
                include_subdirs=False)

    assert os.path.isfile(target), 'Target {} does not exist.'.format(target)

    return


def test_mf2005():
    target = config.target_release
    assert os.path.isfile(target), 'Target {} does not exist.'.format(target)
    target = config.target_previous
    assert os.path.isfile(target), 'Target {} does not exist.'.format(target)

    namefiles = get_namefiles(config.testpaths[0], exclude=config.exclude)
    for namefile in namefiles:
        yield run_mf2005, namefile
    return


def test_teardown():
    if os.path.isfile(config.target_previous):
        print('Removing ' + config.target_previous)
        os.remove(config.target_previous)

    if os.path.isfile(config.target_release):
        print('Removing ' + config.target_release)
        os.remove(config.target_release)

    # remove release source files if target was built
    if os.path.isdir(config.dir_release):
        print('Removing folder ' + config.dir_release)
        shutil.rmtree(config.dir_release)

    # remove previous release source files if target was built
    if os.path.isdir(config.dir_previous):
        print('Removing folder ' + config.dir_previous)
        shutil.rmtree(config.dir_previous)

    return


if __name__ == '__main__':
    test_compile_ref()
    test_compile_prev()

    namefiles = get_namefiles(config.testpaths[0], exclude=config.exclude)
    for namefile in namefiles:
        run_mf2005(namefile)

    test_teardown()
