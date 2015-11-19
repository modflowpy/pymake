from __future__ import print_function
import os
import shutil
import pymake
import flopy

# set up paths
dstpth = os.path.join('temp')
if not os.path.exists(dstpth):
    os.makedirs(dstpth)
mfpth = os.path.join(dstpth, 'MF2005.1_11u')
expth = os.path.join(mfpth, 'test-run')
deppth = os.path.join(mfpth, 'dependencies')

exe_name = 'mf2005r'
srcpth = os.path.join(mfpth, 'src')
target = os.path.join(dstpth, exe_name)

def get_namefiles():
    exclude_tests = ('MNW2-Fig28')
    namefiles = pymake.get_namefiles(expth, exclude=exclude_tests)
    simname = pymake.get_sim_name(namefiles, rootpth=expth)
    return zip(namefiles, simname)

def compile_code():
    # Download the MODFLOW-2005 distribution
    url = 'http://water.usgs.gov/ogw/modflow/MODFLOW-2005_v1.11.00/mf2005v1_11_00_unix.zip'
    pymake.download_and_unzip(url, pth=dstpth)

    # Remove the existing MF2005.1_11u directory if it exists
    if os.path.isdir(mfpth):
        print('Removing folder ' + mfpth)
        shutil.rmtree(mfpth)
    # Rename Unix to a more reasonable name
    os.rename(os.path.join(dstpth, 'Unix'), mfpth)

    # compile modflow
    pymake.main(srcpth, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=False, debug=False,
                include_subdirs=False)
    assert os.path.isfile(target) is True, 'Target does not exist.'

def run_modflow2005(namepth, dst):
    # setup
    testpth = os.path.join(dstpth, dst)
    pymake.setup(namepth, testpth)

    # run test models
    print('running model...{}'.format(namepth))
    epth = os.path.abspath(target)
    success, buff = flopy.run_model(epth, os.path.basename(namepth),
                                    model_ws=testpth, silent=True)
    if success:
        pymake.teardown(testpth)

    assert success is True

def clean_up():
    # clean up
    print('Removing folder ' + mfpth)
    shutil.rmtree(mfpth)
    print('Removing ' + target)
    os.remove(target)

def build_modflow2005_dependency_graphs():

    # build dependencies output directory
    if not os.path.exists(deppth):
        os.makedirs(deppth)
    # build dependency graphs
    print('building dependency graphs')
    pymake.make_plots(srcpth, deppth)
    # test that the dependency figure for the MODFLOW-2005 main exists
    findf = os.path.join(deppth, 'mf2005.f.png')
    assert os.path.isfile(findf) is True

def test_compile():
    # compile MODFLOW-2005
    yield compile_code

def test_modflow2005():
    namefiles = get_namefiles()
    # run models
    for namepth, dst in namefiles:
        yield run_modflow2005, namepth, dst

def test_dependency_graphs():
    # build dependency graphs
    yield build_modflow2005_dependency_graphs

def test_clean_up():
    yield clean_up

if __name__ == '__main__':
    # compile MODFLOW-2005
    compile_code()
    # get namefiles
    namefiles = get_namefiles()
    # run models
    for namepth, dst in namefiles:
        run_modflow2005(namepth, dst)
    # build dependency graphs
    build_modflow2005_dependency_graphs()
    # clean up
    clean_up()

