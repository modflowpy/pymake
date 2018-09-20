
# Build the executables that are used in the flopy autotests
import os
import sys
import shutil
import platform
import subprocess
import flopy

try:
    import pymake
except:
    print('pymake is not installed...will not build executables')
    pymake = None

fc = 'gfortran'
cc = 'gcc'

# bindir should be in the user path to run flopy tests with appropriate
# executables
#
  

# by default bindir will be in user directory unless --root command
# line argument is passed
# On windows will be C:\\Users\\username\\.local\\bin
# On linux and osx will be /Users/username/.local/bin
bindir = None
for idx, arg in enumerate(sys.argv):
    if '--root' in arg.lower():
        bindir = '.'
    elif '--appdir' in arg.lower():
        bindir = sys.argv[idx+1]
        if not os.path.isdir(bindir):
            os.mkdir(bindir)
if bindir is None:
    bindir = os.path.join(os.path.expanduser('~'), '.local', 'bin')
    bindir = os.path.abspath(bindir)
if not os.path.isdir(bindir):
    bindir = '.'
print('targets will be placed the directory:\n    {}\n'.format(bindir))


def create_dir(pth):
    # remove pth directory if it exists
    if os.path.exists(pth):
        print('removing... {}'.format(os.path.abspath(pth)))
        shutil.rmtree(pth)
    # create pth directory
    print('creating... {}'.format(os.path.abspath(pth)))
    os.makedirs(pth)

    msg = 'could not create... {}'.format(os.path.abspath(pth))
    assert os.path.exists(pth), msg
    
    return


def test_create_dirs():
    pths = [os.path.join('..', 'bin'),
            os.path.join('temp')]

    for pth in pths:
        create_dir(pth)

    return


def set_compiler(starget):
    fct = fc
    cct = cc
    # parse command line arguments to see if user specified options
    # relative to building the target
    msg = ''
    for idx, arg in enumerate(sys.argv):
        if arg.lower() == '--ifort':
            if len(msg) > 0:
                msg += '\n'
            msg += '{} - '.format(arg.lower()) + \
                   '{} will be built with ifort.'.format(starget)
            fct = 'ifort'
        elif arg.lower() == '--icc':
            if len(msg) > 0:
                msg += '\n'
            msg += '{} - '.format(arg.lower()) + \
                   '{} will be built with icc.'.format(starget)
            cct = 'icc'
        elif arg.lower() == '--cl':
            if len(msg) > 0:
                msg += '\n'
            msg += '{} - '.format(arg.lower()) + \
                   '{} will be built with cl.'.format(starget)
            cct = 'cl'
        elif arg.lower() == '--clang':
            if len(msg) > 0:
                msg += '\n'
            msg += '{} - '.format(arg.lower()) + \
                   '{} will be built with clang.'.format(starget)
            cct = 'clang'
    if len(msg) > 0:
        print(msg)

    return fct, cct


def set_dbl(target):
    isdbl = False
    for idx, arg in enumerate(sys.argv):
        if arg.lower() == '-dbl' or arg.lower() == '--double':
            target += 'dbl'
            isdbl = True
    return isdbl, target


def set_arch():
    arch = 'intel64'
    for idx, arg in enumerate(sys.argv):
        if arg.lower() == '--ia32':
            arch = 'ia32'
    return arch


def build_target(starget, exe_name, url, dirname, srcname='src',
                 replace_function=None, verify=True, keep=True,
                 dble=None, include_subdirs=False):
    print('Determining if {} needs to be built'.format(starget))
    
    # update exe_name, if necessary, and set double (dble) flag
    if dble is None:
        dble, exe_name = set_dbl(exe_name)
    if platform.system().lower() == 'windows':
        exe_name += '.exe'

    # set compiler
    fct, cct = set_compiler(starget)
    
    # set up architecture
    arch = set_arch()

    # set up target
    target = os.path.abspath(os.path.join(bindir, exe_name))

    # test if executable exists
    epth = exe_name
    for idx, arg in enumerate(sys.argv):
        if '--root' in arg.lower() or '--appdir' in arg.lower():
            epth = target
            
    exe_exists = flopy.which(epth)
    if exe_exists is not None and keep:
        print('No need to build {}'.format(starget) +
              ' since it exists in the current path')
        return

    # get current directory
    cpth = os.getcwd()

    # create temporary path
    dstpth = os.path.join('tempbin')
    print('create...{}'.format(dstpth))
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)
    os.chdir(dstpth)

    # Download the distribution
    pymake.download_and_unzip(url, verify=verify)

    # Set srcdir name
    srcdir = os.path.join(dirname, srcname)

    if replace_function is not None:
        replace_function(srcdir)

    # compile code
    print('compiling...{}'.format(os.path.relpath(target)))
    pymake.main(srcdir, target, fct, cct, makeclean=True,
                expedite=False, dryrun=False, double=dble, debug=False,
                include_subdirs=include_subdirs, arch=arch)

    # change back to original path
    os.chdir(cpth)

    # Clean up downloaded directory
    print('delete...{}'.format(dstpth))
    if os.path.isdir(dstpth):
        try:
            shutil.rmtree(dstpth)
        except:
            pass

    msg = '{} does not exist.'.format(os.path.relpath(target))
    assert os.path.isfile(target), msg

    return
    
    
def update_mt3dfiles(srcdir):
    # Replace the getcl command with getarg
    f1 = open(os.path.join(srcdir, 'mt3dms5.for'), 'r')
    f2 = open(os.path.join(srcdir, 'mt3dms5.for.tmp'), 'w')
    for line in f1:
        f2.write(line.replace('CALL GETCL(FLNAME)', 'CALL GETARG(1,FLNAME)'))
    f1.close()
    f2.close()
    os.remove(os.path.join(srcdir, 'mt3dms5.for'))
    shutil.move(os.path.join(srcdir, 'mt3dms5.for.tmp'),
                os.path.join(srcdir, 'mt3dms5.for'))

    # Replace filespec with standard fortran
    l = '''
          CHARACTER*20 ACCESS,FORM,ACTION(2)
          DATA ACCESS/'STREAM'/
          DATA FORM/'UNFORMATTED'/
          DATA (ACTION(I),I=1,2)/'READ','READWRITE'/
    '''
    fn = os.path.join(srcdir, 'FILESPEC.INC')
    f = open(fn, 'w')
    f.write(l)
    f.close()

    return


def update_seawatfiles(srcdir):
    # rename all source files to lower case so compilation doesn't
    # bomb on case-sensitive operating systems
    srcfiles = os.listdir(srcdir)
    for filename in srcfiles:
        src = os.path.join(srcdir, filename)
        dst = os.path.join(srcdir, filename.lower())
        if 'linux' in sys.platform or 'darwin' in sys.platform:
            os.rename(src, dst)
    if 'linux' in sys.platform or 'darwin' in sys.platform:
        updfile = False
        for idx, arg in enumerate(sys.argv):
            if '--icc' in arg or '--clang' in arg:
                updfile = True
                break
        if updfile:
            fpth = os.path.join(srcdir, 'gmg1.f')
            lines = [line.rstrip() for line in open(fpth)]
            f = open(fpth, 'w')
            for line in lines:
                if "      !DEC$ ATTRIBUTES ALIAS:'_resprint' :: RESPRINT" in line:
                    line = "C      !DEC$ ATTRIBUTES ALIAS:'_resprint' :: RESPRINT"
                f.write('{}\n'.format(line))
            f.close()
    else:
        # must be windows
        if set_arch() == 'intel64':
            fpth = os.path.join(srcdir, 'gmg1.f')
            lines = [line.rstrip() for line in open(fpth)]
            f = open(fpth, 'w')
            for line in lines:
                # comment out the 32 bit one and activate the 64 bit line
                if "C      !DEC$ ATTRIBUTES ALIAS:'resprint' :: RESPRINT" in line:
                    line = "       !DEC$ ATTRIBUTES ALIAS:'resprint' :: RESPRINT"
                if "      !DEC$ ATTRIBUTES ALIAS:'_resprint' :: RESPRINT" in line:
                    line = "C      !DEC$ ATTRIBUTES ALIAS:'_resprint' :: RESPRINT"
                f.write('{}\n'.format(line))
            f.close()
            
    return


def update_mf2000files(srcdir):
    # Remove six src folders
    dlist = ['beale2k', 'hydprgm', 'mf96to2k', 'mfpto2k', 'resan2k', 'ycint2k']
    for d in dlist:
        dname = os.path.join(srcdir, d)
        if os.path.isdir(dname):
            print('Removing ', dname)
            shutil.rmtree(os.path.join(srcdir, d))

    # Move src files and serial src file to src directory
    tpth = os.path.join(srcdir, 'mf2k')
    files = [f for f in os.listdir(tpth) if
             os.path.isfile(os.path.join(tpth, f))]
    for f in files:
        shutil.move(os.path.join(tpth, f), srcdir)
    tpth = os.path.join(srcdir, 'mf2k', 'serial')
    files = [f for f in os.listdir(tpth) if
             os.path.isfile(os.path.join(tpth, f))]
    for f in files:
        shutil.move(os.path.join(tpth, f), srcdir)

    # Remove mf2k directory in source directory
    tpth = os.path.join(srcdir, 'mf2k')
    shutil.rmtree(tpth)


def update_mp6files(srcdir):
    fname1 = os.path.join(srcdir, 'MP6Flowdata.for')
    f = open(fname1, 'r')

    fname2 = os.path.join(srcdir, 'MP6Flowdata_mod.for')
    f2 = open(fname2, 'w')
    for line in f:
        line = line.replace('CD.QX2', 'CD%QX2')
        f2.write(line)
    f.close()
    f2.close()
    os.remove(fname1)

    fname1 = os.path.join(srcdir, 'MP6MPBAS1.for')
    f = open(fname1, 'r')

    fname2 = os.path.join(srcdir, 'MP6MPBAS1_mod.for')
    f2 = open(fname2, 'w')
    for line in f:
        line = line.replace('MPBASDAT(IGRID)%NCPPL=NCPPL',
                            'MPBASDAT(IGRID)%NCPPL=>NCPPL')
        f2.write(line)
    f.close()
    f2.close()
    os.remove(fname1)


def test_build_modflow():
    if pymake is None:
        return
    starget = 'MODFLOW-2005'
    exe_name = 'mf2005'
    dirname = 'MF2005.1_12u'
    url = "https://water.usgs.gov/ogw/modflow/MODFLOW-2005_v1.12.00/MF2005.1_12u.zip"

    build_target(starget, exe_name, url, dirname)

    return


def test_build_mfnwt():
    if pymake is None:
        return
    starget = 'MODFLOW-NWT'
    exe_name = 'mfnwt'
    dirname = 'MODFLOW-NWT_1.1.4'
    url = "http://water.usgs.gov/ogw/modflow-nwt/{0}.zip".format(dirname)

    build_target(starget, exe_name, url, dirname)

    return


def test_build_usg():
    if pymake is None:
        return
    starget = 'MODFLOW-USG'
    exe_name = 'mfusg'
    dirname = 'mfusg.1_3'
    url = 'https://water.usgs.gov/ogw/mfusg/{0}.zip'.format(dirname)

    build_target(starget, exe_name, url, dirname)
    return


def test_build_mf6():
    if pymake is None:
        return
    starget = 'MODFLOW6'
    exe_name = 'mf6'
    dirname = 'mf6.0.3'
    url = 'https://water.usgs.gov/ogw/modflow/{0}.zip'.format(dirname)

    build_target(starget, exe_name, url, dirname, 
                 dble=False, include_subdirs=True)
    return


def test_build_mflgr():
    if pymake is None:
        return
    starget = 'MODFLOW-LGR'
    exe_name = 'mflgr'
    dirname = 'mflgr.2_0'
    url = "https://water.usgs.gov/ogw/modflow-lgr/modflow-lgr-v2.0.0/mflgrv2_0_00.zip"

    build_target(starget, exe_name, url, dirname)
    return


def test_build_mf2000():
    if pymake is None:
        return
    starget = 'MODFLOW-2000'
    exe_name = 'mf2000'
    dirname = 'mf2k.1_19'
    url = "https://water.usgs.gov/nrp/gwsoftware/modflow2000/mf2k1_19_01.tar.gz"

    build_target(starget, exe_name, url, dirname,
                 replace_function=update_mf2000files)
    return


def test_build_mt3dusgs():
    if pymake is None:
        return
    starget = 'MT3D-USGS'
    exe_name = 'mt3dusgs'
    dirname = 'mt3d-usgs_Distribution'
    url = "https://water.usgs.gov/ogw/mt3d-usgs/mt3d-usgs_1.0.zip"

    build_target(starget, exe_name, url, dirname)
    return


def test_build_mt3dms():
    if pymake is None:
        return
    starget = 'MT3DMS'
    exe_name = 'mt3dms'
    dirname = '.'
    url = "http://hydro.geo.ua.edu/mt3d/mt3dms_530.exe"

    build_target(starget, exe_name, url, dirname,
                 srcname=os.path.join('src', 'standard'),
                 verify=False,
                 replace_function=update_mt3dfiles)
    return


def test_build_seawat():
    if pymake is None:
        return
    starget = 'SEAWAT'
    exe_name = 'swt_v4'
    dirname = 'swt_v4_00_05'
    url = "https://water.usgs.gov/ogw/seawat/{0}.zip".format(dirname)

    build_target(starget, exe_name, url, dirname,
                 srcname='source',
                 replace_function=update_seawatfiles,
                 dble=True, keep=True)
    return


def test_build_modpath6():
    if pymake is None:
        return
    starget = 'MODPATH 6'
    exe_name = 'mp6'
    dirname = 'modpath.6_0'
    url = "https://water.usgs.gov/ogw/modpath/archive/modpath_v6.0.01/modpath.6_0_01.zip"

    build_target(starget, exe_name, url, dirname,
                 replace_function=update_mp6files,
                 keep=True)
    return


if __name__ == '__main__':
    test_build_seawat()
    test_build_mf2000()
    test_build_mf6()
    test_build_modflow()
    test_build_mfnwt()
    test_build_modpath6()
    test_build_usg()
    test_build_mt3dms()
    test_build_mt3dusgs()
    test_build_mflgr()
