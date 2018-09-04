from __future__ import print_function
import os
import shutil
import pymake
import flopy

# set up paths
dstpth = os.path.join('temp')
if not os.path.exists(dstpth):
    os.makedirs(dstpth)
#https://water.usgs.gov/ogw/modflow/mf6.0.3.zip
mf6ver = 'mf6.0.3'
mf6pth = os.path.join(dstpth, mf6ver)
expth = os.path.join(mf6pth, 'examples')

exe_name = 'mf6'
srcpth = os.path.join(mf6pth, 'src')
target = os.path.join(dstpth, exe_name)

def get_example_dirs():
    exdirs = [o for o in os.listdir(expth)
              if os.path.isdir(os.path.join(expth, o))]
    return exdirs

def compile_code():
    # Remove the existing mf6 directory if it exists
    if os.path.isdir(mf6pth):
        shutil.rmtree(mf6pth)

    # Download the MODFLOW 6 distribution
    url = 'https://water.usgs.gov/ogw/modflow/{}.zip'.format(mf6ver)
    pymake.download_and_unzip(url, pth=dstpth)

    # compile MODFLOW 6
    pymake.main(srcpth, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=False, debug=False,
                include_subdirs=True)
    assert os.path.isfile(target), 'Target does not exist.'


def clean_up():
    # clean up
    print('Removing folder ' + mf6pth)
    shutil.rmtree(mf6pth)
    print('Removing ' + target)
    os.remove(target)
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
    success, buff = flopy.run_model(epth, 'mfsim.nam',
                                    model_ws=testpth, silent=True)
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
