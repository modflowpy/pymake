from __future__ import print_function
import os
import shutil
import pymake

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

    assert os.path.isfile(target) is True

def get_namefiles():
    namefiles = []
    exclude = ('MNW2-Fig28.nam')
    for file in os.listdir(os.path.join(mfpth, 'test-run')):
        if file.endswith('.nam'):
            if file not in exclude:
                namefiles.append(file)
    return namefiles

def run_modflow2005(namefile):

    root = os.path.splitext(namefile)[0]

    # setup
    testpth = os.path.join(dstpth, root)
    pymake.setup(os.path.join(expth, namefile), testpth)

    # run test models
    print('running model...{}'.format(namefile))
    epth = os.path.join('..', exe_name)
    success, buff = pymake.run_model(epth, namefile, model_ws=testpth, silent=True)

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
    pymake.visualize.make_plots(srcpth, deppth)
    # test that the dependency figure for the MODFLOW-2005 main exists
    findf = os.path.join(deppth, 'mf2005.f.png')
    assert os.path.isfile(findf) is True

def test_modflow2005():
    compile_code()
    namefiles = get_namefiles()
    # run models
    for namefile in namefiles:
        yield run_modflow2005, namefile

def test_dependency_graphs():
    # build dependency graphs
    yield build_modflow2005_dependency_graphs

def test_clean_up():
    yield clean_up

if __name__ == '__main__':
    compile_code()
    namefiles = get_namefiles()
    # run models
    for namefile in namefiles:
        run_modflow2005(namefile)
    # build dependency graphs
    build_mf2005_dependency_graphs()
    # clean up
    clean_up()

