from __future__ import print_function
import os
import shutil
import pymake
import flopy

# set up paths
dstpth = os.path.join('temp')
if not os.path.exists(dstpth):
    os.makedirs(dstpth)
mp7pth = os.path.join(dstpth, 'modpath_7_2_001')
expth = os.path.join(mp7pth, 'examples')

exe_name = 'mp7'
srcpth = os.path.join(mp7pth, 'source')
target = os.path.join(dstpth, exe_name)


def compile_code():
    # Remove the existing modpath6 directory if it exists
    if os.path.isdir(mp7pth):
        shutil.rmtree(mp7pth)

    # Download the MODPATH 7 distribution
    url = "https://water.usgs.gov/ogw/modpath/modpath_7_2_001.zip"
    pymake.download_and_unzip(url, pth=dstpth)

    # allow line lengths greater than 132 columns
    fflags = 'ffree-line-length-512'

    # make modpath 7
    pymake.main(srcpth, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=False, debug=False,
                fflags=fflags)

    assert os.path.isfile(target), 'Target does not exist.'


def get_simfiles():
    edirs = [name for name in os.listdir(expth) if
             os.path.isdir(os.path.join(expth, name))]
    pths = [os.path.join(expth, edir) for edir in edirs]
    dirs = []
    for pth in pths:
        for name in os.listdir(pth):
            if os.path.isdir(os.path.join(pth, name)):
                dirs.append(os.path.join(pth, name))
    simfiles = []
    for d in dirs:
        pth = os.path.join(d, 'original')
        simfiles += [os.path.join(pth, f) for f in os.listdir(pth) if
                     f.endswith('.mpsim')]
    return simfiles

def replace_files():
    return

def run_modpath7(fn):
    # run the model
    print('running model...{}'.format(fn))
    exe = os.path.abspath(target)
    fpth = os.path.basename(fn)
    model_ws = os.path.dirname(fn)
    success, buff = flopy.run_model(exe, fpth, model_ws=model_ws, silent=False)
    assert success, 'could not run...{}'.format(os.path.basename(fn))
    return


def clean_up():
    # clean up
    print('Removing folder ' + mp7pth)
    shutil.rmtree(mp7pth)
    print('Removing ' + target)
    os.remove(target)
    return


def test_compile():
    # compile MODPATH 7
    compile_code()


def test_modpath7():
    simfiles = get_simfiles()
    replace_files()
    for fn in simfiles:
        yield run_modpath7, fn


def test_clean_up():
    yield clean_up
    return


if __name__ == "__main__":
    compile_code()
    simfiles = get_simfiles()
    replace_files()
    for fn in simfiles:
        run_modpath7(fn)
    clean_up()
