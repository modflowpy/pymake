from __future__ import print_function
import os
import shutil
import pymake
import flopy

# define program data
target = 'mp7'
prog_dict = pymake.usgs_prog_data().get_target(target)

# set up paths
dstpth = os.path.join('temp')
if not os.path.exists(dstpth):
    os.makedirs(dstpth)

mp7pth = os.path.join(dstpth, prog_dict.dirname)
emp7 = os.path.abspath(os.path.join(dstpth, target))

mf2005_target = 'mf2005'
temp_dict = pymake.usgs_prog_data().get_target(mf2005_target)
mf2005pth = os.path.join(dstpth, temp_dict.dirname)
emf2005 = os.path.abspath(os.path.join(dstpth, mf2005_target))

mfusg_target = 'mfusg'
temp_dict = pymake.usgs_prog_data().get_target(mfusg_target)
mfusgpth = os.path.join(dstpth, temp_dict.dirname)
emfusg = os.path.abspath(os.path.join(dstpth, mfusg_target))

mf6_target = 'mf6'
temp_dict = pymake.usgs_prog_data().get_target(mf6_target)
mf6pth = os.path.join(dstpth, temp_dict.dirname)
emf6 = os.path.abspath(os.path.join(dstpth, mf6_target))

# MODPATH 7 examples
expth = os.path.join(mp7pth, 'examples')

# set up pths and exes
pths = [mp7pth, mf2005pth, mfusgpth, mf6pth]
exes = [emp7, emf2005, emfusg, emf6]


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
        exe = emf2005
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
        exe = emfusg
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
        exe = emf6
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

    # run the modpath model
    print('running model...{}'.format(fn))
    exe = emp7
    fpth = os.path.basename(fn)
    success, buff = flopy.run_model(exe, fpth, model_ws=model_ws, silent=False)
    assert success, 'could not run...{}'.format(os.path.basename(fn))
    return


def clean_up(pth, exe):
    # clean up downloaded directories
    if os.path.isdir(pth):
        print('Removing folder ' + pth)
        shutil.rmtree(pth)

    # clean up compiled executables
    if os.path.isfile(exe):
        print('Removing ' + exe)
        os.remove(exe)
    return


def test_compile_mp7():
    # Remove the existing MODPATH 6 directory if it exists
    if os.path.isdir(mp7pth):
        shutil.rmtree(mp7pth)

    # download and compile MODPATH 6
    replace_function = pymake.build_replace(target)
    pymake.build_program(target=target,
                         fflags='-ffree-line-length-512',
                         download_dir=dstpth,
                         exe_dir=dstpth,
                         replace_function=replace_function)
    return


def test_compile_mf2005():
    # Remove the existing MODFLOW-2005 directory if it exists
    if os.path.isdir(mf2005pth):
        shutil.rmtree(mf2005pth)

    # download and compile MODFLOW-2005
    replace_function = pymake.build_replace(mf2005_target)
    pymake.build_program(target=mf2005_target,
                         download_dir=dstpth,
                         exe_dir=dstpth,
                         replace_function=replace_function)
    return


def test_compile_mfusg():
    # Remove the existing MODFLOW-USG directory if it exists
    if os.path.isdir(mfusgpth):
        shutil.rmtree(mfusgpth)

    # download and compile MODFLOW-USG
    replace_function = pymake.build_replace(mfusg_target)
    pymake.build_program(target=mfusg_target,
                         download_dir=dstpth,
                         exe_dir=dstpth,
                         replace_function=replace_function)
    return


def test_compile_mf6():
    # Remove the existing MODFLOW 6 directory if it exists
    if os.path.isdir(mf6pth):
        shutil.rmtree(mf6pth)

    # download and compile MODFLOW 6
    replace_function = pymake.build_replace(mf6_target)
    pymake.build_program(target=mf6_target,
                         include_subdirs=True,
                         download_dir=dstpth,
                         exe_dir=dstpth,
                         replace_function=replace_function)
    return


def test_modpath7():
    simfiles = get_simfiles()
    for fn in simfiles:
        yield run_modpath7, fn


def test_clean_up():
    for pth, exe in zip(pths, exes):
        yield clean_up, pth, exe
    return


if __name__ == "__main__":
    # compile codes
    # mp7
    test_compile_mp7()

    # mf2005
    test_compile_mf2005()

    # mfusg
    test_compile_mfusg()

    # mf6
    test_compile_mf6()

    # test executables
    simfiles = get_simfiles()
    for fn in simfiles:
        run_modpath7(fn)

    # clean up test
    for pth, exe in zip(pths, exes):
        clean_up(pth, exe)
