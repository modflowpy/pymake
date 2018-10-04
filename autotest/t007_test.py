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
mp7url = "https://water.usgs.gov/ogw/modpath/modpath_7_2_001.zip"
expth = os.path.join(mp7pth, 'examples')

exe_name = 'mp7'
srcpth = os.path.join(mp7pth, 'source')
target = os.path.join(dstpth, exe_name)

mf2005pth = 'MF2005.1_12u'
mf2005url = 'https://water.usgs.gov/ogw/modflow/MODFLOW-2005_v1.12.00/MF2005.1_12u.zip'
mfusgpth = 'mfusg.1_3'
mfusgurl = 'https://water.usgs.gov/ogw/mfusg/{0}.zip'.format(mfusgpth)
mf6pth = 'mf6.0.3'
mf6url = 'https://water.usgs.gov/ogw/modflow/{0}.zip'.format(mf6pth)

pths = [mf2005pth, mfusgpth, mf6pth, 'modpath_7_2_001']
urls = [mf2005url, mfusgurl, mf6url, mp7url]
srcdirs = ['src', 'src', 'src', 'source']
exes = ['mf2005', 'mfusg', 'mf6', exe_name]

def compile_code(pth=None, url=None, srcdir=None, exe=None):
    if pth is None:
        pth = mp7pth
    if url is None:
        url = mp7url
    include_subdirs = False
    if exe is None:
        exe = exe_name
    elif 'mf6' in exe:
        include_subdirs = True
    if srcdir is None:
        src = srcpth
        binpth = target
    else:
        src = os.path.join(dstpth, pth, srcdir)
        binpth = os.path.join(dstpth, exe)

    # Remove the existing modpath6 directory if it exists
    if os.path.isdir(pth):
        shutil.rmtree(pth)

    # Download the MODPATH 7 distribution
    pymake.download_and_unzip(url, pth=dstpth)

    # update files
    if exe == exe_name:
        update_files(src)

    # allow line lengths greater than 132 columns
    fflags = 'ffree-line-length-512'

    # make binary file
    pymake.main(src, binpth, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=False, debug=False,
                fflags=fflags, include_subdirs=include_subdirs)

    msg = 'Target ({}) does not exist.'.format(os.path.basename(binpth))
    assert os.path.isfile(binpth), msg


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


def update_files(srcdir):
    fpth = os.path.join(srcdir, 'StartingLocationReader.f90')
    with open(fpth) as f:
        lines = f.readlines()
    f = open(fpth, 'w')
    for line in lines:
        if 'pGroup%Particles(n)%InitialFace = 0' in line:
            continue
        # line = line.replace('pGroup%Particles(n)%InitialFace = 0',
        #                     '! pGroup%Particles(n)%InitialFace = 0')
        f.write(line)
    f.close()
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
                    content[idx] = line.replace(line, srepls[jdx])
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
        exe = os.path.abspath(os.path.join(dstpth, 'mf2005'))
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
        exe = os.path.abspath(os.path.join(dstpth, 'mfusg'))
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
        exe = os.path.abspath(os.path.join(dstpth, 'mf6'))
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


def clean_up(pth, exe):
    # clean up downloaded directories
    pth = os.path.join(dstpth, pth)
    if os.path.isdir(pth):
        print('Removing folder ' + pth)
        shutil.rmtree(pth)
    # clean up compiled executables
    binpth = os.path.join(dstpth, exe)
    if os.path.isfile(binpth):
        print('Removing ' + binpth)
        os.remove(binpth)
    return


def test_compile():
    # compile code
    for pth, url, srcdir, exe in zip(pths, urls, srcdirs, exes):
        yield compile_code, pth, url, srcdir, exe


def test_modpath7():
    simfiles = get_simfiles()
    for fn in simfiles:
        yield run_modpath7, fn


def test_clean_up():
    for pth, exe in zip(pths, exes):
        yield clean_up, pth, exe
    return


if __name__ == "__main__":
    for pth, url, srcdir, exe in zip(pths, urls, srcdirs, exes):
        compile_code(pth=pth, url=url, srcdir=srcdir, exe=exe)
    simfiles = get_simfiles()
    replace_files()
    for fn in simfiles:
        run_modpath7(fn)
    for pth, exe in zip(pths, exes):
        clean_up(pth, exe)
