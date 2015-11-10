from __future__ import print_function
import os
import shutil
import pymake


def test_modflow2005():

    # get current directory
    pth = os.getcwd()
    # working directory
    dstpth = os.path.join('temp')
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)
    # change to temp subdirectory
    os.chdir(dstpth)

    # Download the MODFLOW-2005 distribution
    url = 'http://water.usgs.gov/ogw/modflow/MODFLOW-2005_v1.11.00/mf2005v1_11_00_unix.zip'
    pymake.download_and_unzip(url)

    # Remove the existing MF2005.1_11u directory if it exists
    dirname = os.path.join('MF2005.1_11u')
    if os.path.isdir(dirname):
        shutil.rmtree(dirname)
    # Rename Unix to a more reasonable name
    os.rename(os.path.join('Unix'), os.path.join('MF2005.1_11u'))

    srcdir = os.path.join(dirname, 'src')
    target = 'mf2005pymake'

    # compile modflow
    pymake.main(srcdir, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=False, debug=False,
                include_subdirs=False)

    assert os.path.isfile(target) is True

    # run test models
    model_ws = os.path.join(dirname, 'test-run')
    exe_name = os.path.join(os.getcwd(), target)
    namefiles = []
    exclude = ['MNW2-Fig28.nam']
    for file in os.listdir(model_ws):
        if file.endswith('.nam'):
            namefiles.append(file)
    for namefile in namefiles:
        if namefile in exclude:
            continue
        print('running model...{}'.format(namefile))
        success, buff = pymake.run_model(exe_name, namefile, model_ws=model_ws, silent=True)
        assert success is True

    # change back to the starting directory
    os.chdir(pth)


if __name__ == '__main__':
    test_modflow2005()
