from __future__ import print_function
import os
import shutil
import pymake
import flopy

# set up paths
dstpth = os.path.join('temp')
if not os.path.exists(dstpth):
    os.makedirs(dstpth)
mp6pth = os.path.join(dstpth, 'Modpath_7_1_000')
expth = os.path.join(mp6pth, 'examples')

exe_name = 'mp7'
srcpth = os.path.join(mp6pth, 'source')
target = os.path.join(dstpth, exe_name)


def compile_code():
    # Remove the existing modpath6 directory if it exists
    if os.path.isdir(mp6pth):
        shutil.rmtree(mp6pth)

    # Download the MODFLOW-2005 distribution
    url = "https://water.usgs.gov/ogw/modpath/Modpath_7_1_000.zip"
    pymake.download_and_unzip(url, pth=dstpth)

    # modify source files that prevent compiling with gfortran
    pth = os.path.join(srcpth, 'utl7u1.f')
    if os.path.isfile(pth):
        os.remove(pth)

    fname1 = os.path.join(srcpth, 'ModpathSubCellData.f90')
    f = open(fname1, 'r')
    fname2 = os.path.join(srcpth, 'ModpathSubCellData_mod.f90')
    f2 = open(fname2, 'w')
    for line in f:
        line = line.replace('location.', 'location%')
        f2.write(line)
    f.close()
    f2.close()
    os.remove(fname1)
    os.rename(fname2, fname1)

    fname1 = os.path.join(srcpth, 'ModpathCellData.f90')
    f = open(fname1, 'r')
    fname2 = os.path.join(srcpth, 'ModpathCellData_mod.f90')
    f2 = open(fname2, 'w')
    for line in f:
        line = line.replace('dimension(grid%GetCellCount())', 'dimension(:)')
        line = line.replace('dimension(grid%GetReducedConnectionCount())',
                            'dimension(:)')
        f2.write(line)
    f.close()
    f2.close()
    os.remove(fname1)
    os.rename(fname2, fname1)

    fname1 = os.path.join(srcpth, 'MPath7.f90')
    f = open(fname1, 'r')
    fname2 = os.path.join(srcpth, 'MPath7_mod.f90')
    f2 = open(fname2, 'w')
    for line in f:
        line = line.replace("form='binary', access='stream'",
                            "form='unformatted', access='stream'")
        f2.write(line)
    f.close()
    f2.close()
    os.remove(fname1)
    os.rename(fname2, fname1)

    # allow line lengths greater than 132 columns
    fflags = 'ffree-line-length-512'

    # make modpath 7
    pymake.main(srcpth, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=False, debug=False,
                fflags=fflags)

    assert os.path.isfile(target), 'Target does not exist.'


def get_simfiles():
    dirs = [name for name in os.listdir(expth) if
            os.path.isdir(os.path.join(expth, name))]
    simfiles = []
    for d in dirs:
        pth = os.path.join(expth, d, 'original')
        simfiles += [os.path.join(pth, f) for f in os.listdir(pth) if
                     f.endswith('.mpsim')]
    return simfiles

def replace_files():
    dirs = [name for name in os.listdir(expth) if
            os.path.isdir(os.path.join(expth, name))]
    # rename a few files for linux
    replace_files = ['example_1.BUD', 'Zones_layer_3.txt',
                     'Retardation_layer_1.txt']
    for d in dirs:
        pth = os.path.join(expth, d, 'original')
        for rf in replace_files:
            fname1 = os.path.join(pth, rf)
            if rf in os.listdir(pth):
                fname2 = os.path.join(pth, 'temp')
                print('copy {} to {}'.format(os.path.basename(fname1),
                                             os.path.basename(fname2)))
                shutil.copy(fname1, fname2)
                print('deleting {}'.format(os.path.basename(fname1)))
                os.remove(fname1)
                fname1 = os.path.join(pth, rf.lower())
                print('rename {} to {}'.format(os.path.basename(fname2),
                                               os.path.basename(fname1)))
                os.rename(fname2, fname1)

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
    print('Removing folder ' + mp6pth)
    shutil.rmtree(mp6pth)
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


if __name__ == "__main__":
    compile_code()
    simfiles = get_simfiles()
    replace_files()
    for fn in simfiles:
        run_modpath7(fn)
    clean_up()
