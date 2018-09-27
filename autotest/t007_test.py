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


def replace_data(dpth):
    fpths = [name for name in os.listdir(dpth) if
             os.path.isfile(os.path.join(dpth, name))]
    repl = False
    if 'ex01_mf2005.dis' in fpths:
        sfinds = ['! Example 1: MODFLOW-2005 discretization file']
        srepls = ['# Example 1: MODFLOW-2005 discretization file\n']
        fpth = 'ex01_mf2005.dis'
        repl = True
    elif 'ex04_mf6.disv' in fpths:
        sfinds = ['  OPEN/CLOSE  mptest006_idomain.csv']
        srepls = ['  OPEN/CLOSE  ex04_mf6_idomain.csv\n']
        fpth = 'ex04_mf6.disv'
        repl = True
    elif 'mfsim.nam' in fpths:
        sfinds = ['  TDIS6  ex02a_mf6.tdis',
                  '  GWF6  ex02a_mf6.nam  ex02a_mf6',
                  '  IMS6  ex02a_mf6.ims  ex02a_mf6']
        srepls = ['  TDIS6  ex02_mf6.tdis\n',
                  '  GWF6  ex02_mf6.nam  ex02_mf6\n',
                  '  IMS6  ex02_mf6.ims  ex02_mf6\n']
        fpth = 'mfsim.nam'
        repl = True
    if repl:
        fpth = os.path.join(dpth, fpth)
        with open(fpth, 'r') as f:
            content = f.readlines()
        for idx, line in enumerate(content):
            for jdx, sfind in enumerate(sfinds):
                if sfind in line:
                    print(line)
                    content[idx] = line.replace(line, srepls[jdx])
                    print(content[idx])
        with open(fpth, 'w') as f:
            f.writelines(content)
    return


def set_lowercase(fpth):
    with open(fpth, 'r') as f:
        content = f.readlines()
    for idx, line in enumerate(content):
        content[idx] = line.lower()
    with open(fpth, 'w') as f:
        f.writelines(content)
    return


def run_modpath7(fn):
    model_ws = os.path.dirname(fn)
    # run the flow model
    run = True
    if 'modflow-2005' in fn.lower():
        exe = 'mf2005'
        v = flopy.which(exe)
        if v is None:
            run = False
        nam = [name for name in os.listdir(model_ws) if '.nam' in name.lower()]
        if len(nam) > 0:
            fpth = nam[0]
            # read and rewrite the name file
            set_lowercase(os.path.join(model_ws, fpth))
        else:
            fpth = None
            run = False
    elif 'modflow-usg' in fn.lower():
        exe = 'mfusg'
        v = flopy.which(exe)
        if v is None:
            run = False
        nam = [name for name in os.listdir(model_ws) if '.nam' in name.lower()]
        if len(nam) > 0:
            fpth = nam[0]
        else:
            fpth = None
            run = False
    elif 'modflow-6' in fn.lower():
        exe = 'mf6'
        v = flopy.which(exe)
        if v is None:
            run = False
        fpth = None
    else:
        run = False
    if run:
        # fix any known problems
        replace_data(model_ws)
        # run the model
        msg = '{}'.format(exe)
        if fpth is not None:
            msg += ' {}'.format(os.path.basename(fpth))
        success, buff = flopy.run_model(exe, fpth, model_ws=model_ws,
                                        silent=False)
        assert success, 'could not run...{}'.format(msg)
    # run the model
    print('running model...{}'.format(fn))
    exe = os.path.abspath(target)
    fpth = os.path.basename(fn)
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
