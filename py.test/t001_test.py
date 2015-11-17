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

exe_name = 'mf2005r'
srcdir = os.path.join(mfpth, 'src')
target = os.path.join(dstpth, exe_name)


def compile_code():
    # Download the MODFLOW-2005 distribution
    url = 'http://water.usgs.gov/ogw/modflow/MODFLOW-2005_v1.11.00/mf2005v1_11_00_unix.zip'
    pymake.download_and_unzip(url, pth=dstpth)

    # Remove the existing MF2005.1_11u directory if it exists
    if os.path.isdir(mfpth):
        shutil.rmtree(mfpth)
    # Rename Unix to a more reasonable name
    os.rename(os.path.join(dstpth, 'Unix'), mfpth)

    # compile modflow
    pymake.main(srcdir, target, 'gfortran', 'gcc', makeclean=True,
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
    pymake.setup(namefile, expth, testpth)

    # run test models
    print('running model...{}'.format(namefile))
    epth = os.path.join('..', exe_name)
    success, buff = pymake.run_model(epth, namefile, model_ws=testpth, silent=True)

    if success:
        pymake.teardown(testpth)

    assert success is True

def test_modflow2005():
    #compile_code()
    namefiles = get_namefiles()
    for namefile in namefiles:
        yield run_modflow2005, namefile

if __name__ == '__main__':
    #compile_code()
    namefiles = get_namefiles()
    for namefile in namefiles:
        run_modflow2005(namefile)
