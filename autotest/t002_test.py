from __future__ import print_function
import os
import sys
import shutil

import pymake
import flopy

# define program data
target = 'swtv4'
if sys.platform.lower() == 'win32':
    target += '.exe'

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join('temp')
if not os.path.exists(dstpth):
    os.makedirs(dstpth)

swtpth = os.path.join(dstpth, prog_dict.dirname)
expth = os.path.join(swtpth, 'examples')
deppth = os.path.join(swtpth, 'dependencies')

srcpth = os.path.join(swtpth, prog_dict.srcdir)
epth = os.path.abspath(os.path.join(dstpth, target))


def edit_namefile(namefile):
    # read existing namefile
    f = open(namefile, 'r')
    lines = f.read().splitlines()
    f.close()
    # remove global line
    f = open(namefile, 'w')
    for line in lines:
        if 'global' in line.lower():
            continue
        f.write('{}\n'.format(line))
    f.close()


def get_namefiles():
    if os.path.exists(epth):
        exclude_tests = ('7_swtv4_ex', '6_rotation')
        namefiles = pymake.get_namefiles(expth, exclude=exclude_tests)
        simname = pymake.get_sim_name(namefiles, rootpth=expth)
    else:
        namefiles = [None]
        simname = [None]
    return zip(namefiles, simname)


def compile_code():
    # Remove the existing seawat directory if it exists
    if os.path.isdir(swtpth):
        shutil.rmtree(swtpth)

    # compile seawat
    replace_function = pymake.build_replace(target)
    pymake.build_program(target=target,
                         double=True,
                         download_dir=dstpth,
                         exe_dir=dstpth,
                         replace_function=replace_function,
                         modify_exe_name=False)

    return


def clean_up():
    # clean up downloaded directory
    print('Removing folder ' + swtpth)
    if os.path.isdir(swtpth):
        shutil.rmtree(swtpth)

    # clean up target
    print('Removing ' + target)
    if os.path.isfile(epth):
        os.remove(epth)

    return


def run_seawat(namepth, dst):
    if namepth is not None:
        print('running...{}'.format(dst))
        # setup
        testpth = os.path.join(dstpth, dst)
        pymake.setup(namepth, testpth)

        # edit name file
        pth = os.path.join(testpth, os.path.basename(namepth))
        edit_namefile(pth)

        # run test models
        if os.path.exists(epth):
            print('running model...{}'.format(os.path.basename(namepth)))
            success, buff = flopy.run_model(epth, os.path.basename(namepth),
                                            model_ws=testpth, silent=True)
        if success:
            pymake.teardown(testpth)
        else:
            errmsg = 'could not run...{}'.format(os.path.basename(namepth))
    else:
        success = False
        errmsg = '{} does not exist'.format(epth)

    assert success, errmsg

    return


def build_seawat_dependency_graphs():
    if os.path.exists(epth):

        # build dependencies output directory
        if not os.path.exists(deppth):
            os.makedirs(deppth)

        # build dependency graphs
        print('building dependency graphs')
        pymake.visualize.make_plots(srcpth, deppth)

        # test that the dependency figure for the SEAWAT main exists
        findf = os.path.join(deppth, 'swt_v4.f.png')
        success = os.path.isfile(findf)
        assert success, 'could not find {}'.format(findf)
    else:
        success = False

    assert success, 'could not build dependency graphs'

    return


def test_compile():
    # compile seawat
    yield compile_code


def test_seawat():
    # get name files and simulation name
    namefiles = get_namefiles()

    # run models
    for namepth, dst in namefiles:
        yield run_seawat, namepth, dst


def test_dependency_graphs():
    try:
        import pydotplus.graphviz as pydot
        # build dependency graphs
        yield build_seawat_dependency_graphs
    except:
        print('pymake graphing capabilities not available.')


def test_clean_up():
    yield clean_up


if __name__ == '__main__':
    # compile seawat
    compile_code()

    # get name files and simulation name
    namefiles = get_namefiles()

    # run models
    for namepth, dst in namefiles:
        run_seawat(namepth, dst)

    # build dependency graphs
    build_seawat_dependency_graphs()

    # clean up
    clean_up()
