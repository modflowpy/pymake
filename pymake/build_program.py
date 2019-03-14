import os
import sys
import shutil
import platform
import types
from datetime import datetime

import flopy

from .pymake import main
from .download import download_and_unzip
from .usgsurls import usgs_prog_data


def get_function_names(module, select_name=None):
    """
    Get a dictionary of functions available in a user-specified source file.
    This function was developed to create a dictionary of functions in this
    source file (build_program.py). Optionally, the user can get a get a
    dictionary of functions that contain a specific text string in the name.

    Parameters
    ----------
    module : module
        module to evaluate function names
    select_name : str
        string that is used to select a subset of the available functions in
        the module

    Returns
    -------
    func : dict
        dictionary with function name keys and values set to function pointers

    """
    func = {}
    for key, value in module.__dict__.items():
        ladd = False
        if type(value) is types.FunctionType:
            if select_name is None:
                ladd = True
            else:
                if select_name in value.__name__:
                    ladd = True
            if ladd:
                func[value.__name__] = value
    return func


def set_bindir(target):
    """
    Set path for target based on --travis or --appdir command line arguments

    Parameters
    ----------
    target : str
        target to build


    Returns
    -------
    bindir : str
        path to build application in. By default, bindir will be in the
        current directory ('.'). Passing --travis command line argument will
        set bindir to C:\\Users\\username\\.local\\bin on windows and
        /Users/username/.local/bin on Linux and OSX. Passing --appdir bindir
        command line argument will set bindir to user-defined path

    """
    bindir = None
    for idx, arg in enumerate(sys.argv):
        if '--travis' in arg.lower():
            bindir = os.path.join(os.path.expanduser('~'), '.local', 'bin')
            bindir = os.path.abspath(bindir)
        elif '--appdir' in arg.lower():
            bindir = sys.argv[idx + 1]
            if not os.path.isdir(bindir):
                os.mkdir(bindir)
    if bindir is None:
        bindir = '.'
    if not os.path.isdir(bindir):
        bindir = '.'
    print('{} will be placed in the directory:\n'.format(target) +
          '    "{}"\n'.format(bindir))

    return bindir


def set_build(exe_name):
    """
    Set boolean that defines whether the target should be built if it
    already exists based on --keep command line argument

    Parameters
    ----------
    exe_name : str
        executable name that includes double ("dbl"), debug ("d"), and/or
        extension (".exe") based on command line arguments and OS.

    Returns
    -------
    build : bool

    """
    keep = False
    for idx, arg in enumerate(sys.argv):
        if '--keep' in arg.lower():
            keep = True

    build = True
    exe_name = os.path.basename(exe_name)
    if keep:
        print('Determining if {} needs to be built'.format(exe_name))

        exe_exists = flopy.which(exe_name)

        # determine if it is in the current directory
        if exe_exists is None:
            exe_exists = flopy.which('./' + exe_name)

        if exe_exists is not None:
            build = False
            print('No need to build {}'.format(exe_name) +
                  ' since it exists in the current path')
            print('    "{}"'.format(os.path.abspath(exe_exists)))

    return build


def set_compiler(target):
    """
    Set fortran and c compilers based on --ifort, --mpiifort, --icc, --cl,
    and --clang command line arguments

    Parameters
    ----------
    target : str
        target to build

    Returns
    -------
    fc : str
        string denoting the fortran compiler to use. Default is gfortran.
    cc : str
        string denoting the c compiler to use. Default is gcc.

    """
    fc = 'gfortran'
    if target in ['triangle', 'gridgen']:
        fc = None
    cc = 'gcc'
    if target in ['gridgen']:
        cc = 'g++'
    # parse command line arguments to see if user specified options
    # relative to building the target
    for idx, arg in enumerate(sys.argv):
        if arg.lower() == '--ifort' and fc is not None:
            fc = 'ifort'
        elif arg.lower() == '--icc':
            cc = 'icc'
        elif arg.lower() == '--cl':
            cc = 'cl'
        elif arg.lower() == '--clang':
            cc = 'clang'

    msg = '{} fortran code will be built with {}.\n'.format(target, fc)
    msg += '{} c/c++ code will be built with {}.\n'.format(target, cc)
    print(msg)

    return fc, cc


def set_fflags(target):
    """
    Set appropriate fortran compiler flags based on target.

    Parameters
    ----------
    target : str
        target to build

    Returns
    -------
    fflags : str
        fortran compiler flags. Default is None

    """
    fflags = None
    if target == 'mp7':
        fflags = '-ffree-line-length-512'

    return fflags


def set_double(target):
    """
    Set boolean that defines if the target should use double precision reals
    based on -dbl or --double command line arguments.

    Parameters
    ----------
    target : str
        target to build

    Returns
    -------
    double : bool

    """
    double = False
    for idx, arg in enumerate(sys.argv):
        if arg.lower() == '-dbl' or arg.lower() == '--double':
            double = True
            break

    if target in ['swtv4']:
        double = True

    # write a message
    if double:
        msg = '{} will be built using double precision floats.'.format(target)
    else:
        msg = '{} will be built using single precision floats.'.format(target)
    print(msg)

    return double


def set_debug(target):
    """
    Set boolean that defines if the target should be compiled with debug
    compiler options based on -dbg or --debug command line arguments.

    Parameters
    ----------
    target : str
        target to build

    Returns
    -------
    debug : bool

    """
    debug = False
    for idx, arg in enumerate(sys.argv):
        if arg.lower() == '-dbg' or arg.lower() == '--debug':
            debug = True
            break

    # write a message
    if debug:
        msg = '{} will be built with debug flags.'.format(target)
    else:
        msg = '{} will be built as a release application.'.format(target)
    print(msg)

    return debug


def set_arch(target):
    """
    Set architecture to compile target for based on --ia32 command line
    argument. Default architecture is intel64 (64-bit).

    Parameters
    ----------
    target : str
        target to build

    Returns
    -------
    arch : str

    """
    arch = 'intel64'
    for idx, arg in enumerate(sys.argv):
        if arg.lower() == '--ia32':
            arch = 'ia32'

    # set arch to ia32 if building on windows
    if target == 'triangle':
        if platform.system().lower() == 'windows':
            arch = 'ia32'

    # write a message
    msg = '{} will be built for {} architecture.'.format(target, arch)
    print(msg)

    return arch


def build_program(target='mf2005', fc='gfortran', cc='gcc', makeclean=True,
                  expedite=False, dryrun=False, double=False, debug=False,
                  include_subdirs=False, fflags=None, arch='intel64',
                  makefile=False, srcdir2=None, extrafiles=None,
                  exe_name=None, exe_dir=None,
                  replace_function=None, verify=True, modify_exe_name=True,
                  download_dir=None, download=True,
                  download_clean=False, download_verify=True, timeout=30):
    """

    Parameters
    ----------
    target : str

    fc : str
    cc : str
    makeclean : bool
    expedite : bool
    dryrun : bool
    double : bool
    debug : bool
    include_subdirs : bool
    fflags : str or list
    arch : str
    makefile : bool
    srcdir2 : str
    extrafiles : str
    exe_name : str
    exe_dir : str
    replace_function : str
    verify : bool
    modify_exe_name : bool
    download_dir : str
    download : bool
    download_clean : bool
    download_verify : bool
    timeout : int

    Returns
    -------

    """
    # set exe_name
    if exe_name is None:
        exe_name = target

    if modify_exe_name:
        if double:
            filename, file_extension = os.path.splitext(exe_name)
            if 'dbl' not in filename.lower():
                exe_name = filename + 'dbl' + file_extension
        if debug:
            filename, file_extension = os.path.splitext(exe_name)
            if filename.lower()[-1] != 'd':
                exe_name = filename + 'd' + file_extension

    if platform.system().lower() == 'windows':
        filename, file_extension = os.path.splitext(exe_name)
        if file_extension.lower() is not '.exe':
            exe_name += '.exe'

    build = set_build(exe_name)

    if build:
        if exe_dir is not None:
            exe_name = os.path.abspath(os.path.join(exe_dir, exe_name))

        # extract program data for target
        prog_dict = usgs_prog_data.get_target(target)

        # set url
        url = prog_dict.url

        # Set dir name
        dirname = prog_dict.dirname
        if download_dir is None:
            dirname = './'
            download_dir = './'
        else:
            dirname = os.path.join(download_dir, dirname)

        # make the download directory if it does not exist
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        # Set srcdir name
        srcdir = prog_dict.srcdir
        srcdir = os.path.join(dirname, srcdir)

        # Download the distribution
        if download:
            download_and_unzip(url, pth=download_dir, verify=download_verify,
                               timeout=timeout)

        if replace_function is not None:
            print('replacing select source files for {}'.format(target))
            replace_function(srcdir, fc, cc, arch)

        # compile code
        print('compiling...{}'.format(os.path.relpath(exe_name)))
        main(srcdir, exe_name, fc=fc, cc=cc, makeclean=makeclean,
             expedite=expedite, dryrun=dryrun, double=double, debug=debug,
             include_subdirs=include_subdirs, fflags=fflags, arch=arch,
             makefile=makefile, srcdir2=srcdir2, extrafiles=extrafiles)

        if verify:
            app = os.path.relpath(exe_name)
            msg = '{} does not exist.'.format(app)
            assert os.path.isfile(exe_name), msg

        # clean download directory if different than directory with executable
        if download_clean:
            edir = os.path.abspath(os.path.dirname(exe_name))
            ddir = os.path.abspath(download_dir)
            if edir != ddir:
                if os.path.isdir(ddir):
                    shutil.rmtree(ddir)

    return


def build_targets(current=True):
    """
    Build a list of targets

    Parameters
    ----------
    current : bool
        return list of current targets. If current is False, returned list
        will include all available USGS applications included in usgsurls.txt.
        Default is True

    Returns
    -------
    targets : list
        list of targets

    """
    return usgs_prog_data.get_keys(current=current)


def build_replace(targets):
    """
    Get pointers to appropriate replace_function for a target

    Parameters
    ----------
    targets : str or list of str
        targets to determine replace_function function pointers.
    Returns
    -------
    replace_funcs : function pointer or list of function pointers
        None is returned as the function pointer if the target string is
        not in the function name


    """
    if isinstance(targets, str):
        targets = [targets]

    # get a dictionary of update functions
    funcs = get_function_names(sys.modules[__name__], select_name='update_')

    # generate a list of available functions
    replace_funcs = []
    for target in targets:
        f = None
        for key, value in funcs.items():
            if target in key:
                f = value
                break
        replace_funcs.append(f)

    # transform from a list to the function pointer if only one element
    # is in the list
    if len(replace_funcs) == 1:
        replace_funcs = replace_funcs[0]
    return replace_funcs


def build_apps(targets=None):
    """
    Build all of the current targets or a subset of targets

    Parameters
    ----------
    targets : str or list of str
        targets to build. If targets is None, all current targets will
        be build. Default is None

    Returns
    -------

    """
    start_time = datetime.now()
    if targets is None:
        targets = build_targets()
    else:
        if isinstance(targets, str):
            targets = [targets]

    for target in targets:
        start_downcomp = datetime.now()

        # set bindir
        bindir = set_bindir(target)

        # set double precision flag and whether the executable name
        # can be modified
        double = set_double(target)
        if target == 'swtv4':
            modify_exe_name = False
        else:
            modify_exe_name = True

        # set debug flag
        debug = set_debug(target)

        # set
        if target in ['swtv4']:
            modify_exe_name = False

        # set compiler
        fc, cc = set_compiler(target)

        # set fortran flags
        fflags = set_fflags(target)

        # set architecture
        arch = set_arch(target)

        # set include_subdirs
        if target in ['mf6', 'gridgen']:
            include_subdirs = True
        else:
            include_subdirs = False

        # set replace function
        replace_function = build_replace(target)

        # set download information
        if target in ['mt3dms']:
            download_verify = False
            timeout = 10
        else:
            download_verify = True
            timeout = 30

        # build the code
        build_program(target=target,
                      fc=fc,
                      cc=cc,
                      double=double,
                      debug=debug,
                      fflags=fflags,
                      arch=arch,
                      include_subdirs=include_subdirs,
                      replace_function=replace_function,
                      modify_exe_name=modify_exe_name,
                      exe_dir=bindir,
                      download_dir='temp',
                      download_clean=True,
                      download_verify=download_verify,
                      timeout=timeout)

        # calculate download and compile time
        end_downcomp = datetime.now()
        elapsed = end_downcomp - start_downcomp
        print('elapsed download and compile time (hh:mm:ss.ms): ' +
              '{}'.format(elapsed))

    end_time = datetime.now()
    elapsed = end_time - start_time
    print('elapsed time (hh:mm:ss.ms): {}'.format(elapsed))

    return


# routines for updating source files to compile with gfortran
def update_triangle_files(srcdir, fc, cc, arch):
    """
    Update the triangle source files

    Parameters
    ----------
    srcdir : str
    fc : str
    cc : str
    arch : str

    Returns
    -------

    """
    # move the downloaded files
    rootdir = os.path.join(*(srcdir.split(os.path.sep)[:1]))
    prog_dict = usgs_prog_data().get_target('triangle')
    dirname = prog_dict.dirname
    dstpth = os.path.join(rootdir, dirname)

    # make destination directory
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)

    # make src directory
    if not os.path.exists(srcdir):
        os.makedirs(srcdir)

    # move the source files
    src = os.path.join(rootdir, 'triangle.c')
    dst = os.path.join(srcdir, 'triangle.c')
    shutil.move(src, dst)
    src = os.path.join(rootdir, 'triangle.h')
    dst = os.path.join(srcdir, 'triangle.h')
    shutil.move(src, dst)

    return


def update_mt3dms_files(srcdir, fc, cc, arch):
    """
    Update the MT3D source files

    Parameters
    ----------
    srcdir : str
    fc : str
    cc : str
    arch : str

    Returns
    -------

    """
    # move the downloaded files
    rootdir = os.path.join(*(srcdir.split(os.path.sep)[:1]))
    prog_dict = usgs_prog_data().get_target('mt3dms')
    dirname = prog_dict.dirname
    dstpth = os.path.join(rootdir, dirname)

    # Clean up unneeded files
    for f in ['ReadMe_MT3DMS.pdf', 'upgrade.pdf']:
        print('Removing..."{}"'.format(f))
        os.remove(os.path.join(rootdir, f))

    # remove some unneeded folders
    dir_list = ['bin', 'doc', 'examples', 'utility']
    for d in dir_list:
        dname = os.path.join(rootdir, d)
        if os.path.isdir(dname):
            print('Removing..."{}"'.format(dname))
            shutil.rmtree(dname)

    # make destination directory
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)

    # move the files
    for src_dir, dirs, files in os.walk(rootdir):
        # skip target directory (dirname)
        if dirname in src_dir:
            continue
        if src_dir is rootdir:
            continue
        else:
            dst_dir = src_dir.replace(rootdir + os.path.sep, '')
            dst_dir = os.path.join(dstpth, dst_dir)
        if not os.path.exists(dst_dir):
            os.mkdir(dst_dir)
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)
            if os.path.exists(dst_file):
                os.remove(dst_file)
            print('{} -> {}'.format(src_file, dst_dir))
            # shutil.copy(src_file, dst_dir)
            shutil.move(src_file, dst_dir)

    # remove the original source directory
    dname = os.path.join(rootdir, 'src')
    if os.path.isdir(dname):
        print('Removing..."{}"'.format(dname))
        shutil.rmtree(dname)

    # remove some unneeded files
    file_list = ['automake.fig', 'mt3dms5b.exe']
    for f in file_list:
        dname = os.path.join(srcdir, f)
        if os.path.isfile(dname):
            print('Removing..."{}"'.format(dname))
            os.remove(dname)

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

    # Need to initialize the V array in SADV5B
    # see here: https://github.com/MODFLOW-USGS/mt3d-usgs/pull/46
    f1 = open(os.path.join(srcdir, 'mt_adv5.for'), 'r')
    f2 = open(os.path.join(srcdir, 'mt_adv5.for.tmp'), 'w')
    sfind = 'C--SET DT TO NEGATIVE FOR BACKWARD TRACKING'
    sreplace = 'C--INITIALIZE\n      V(:)=0.\nC\n' + sfind
    for line in f1:
        f2.write(line.replace(sfind, sreplace))
    f1.close()
    f2.close()
    os.remove(os.path.join(srcdir, 'mt_adv5.for'))
    shutil.move(os.path.join(srcdir, 'mt_adv5.for.tmp'),
                os.path.join(srcdir, 'mt_adv5.for'))

    return


def update_swtv4_files(srcdir, fc, cc, arch):
    # Remove the parallel and serial folders from the source directory
    dlist = ['parallel', 'serial']
    for d in dlist:
        dname = os.path.join(srcdir, d)
        if os.path.isdir(dname):
            print('Removing..."{}"'.format(dname))
            shutil.rmtree(os.path.join(srcdir, d))

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
        if 'icc' in cc or 'clang' in cc:
            updfile = True
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
        if arch == 'intel64':
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


def update_mf2000_files(srcdir, fc, cc, arch):
    # Remove six src folders
    dlist = ['beale2k', 'hydprgm', 'mf96to2k', 'mfpto2k', 'resan2k', 'ycint2k']
    for d in dlist:
        dname = os.path.join(srcdir, d)
        if os.path.isdir(dname):
            print('Removing..."{}"'.format(dname))
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


def update_mp6_files(srcdir, fc, cc, arch):
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


def update_mp7_files(srcdir, fc, cc, arch):
    fpth = os.path.join(srcdir, 'StartingLocationReader.f90')
    with open(fpth) as f:
        lines = f.readlines()
    f = open(fpth, 'w')
    for line in lines:
        if 'pGroup%Particles(n)%InitialFace = 0' in line:
            continue
        f.write(line)
    f.close()


def update_vs2dt_files(srcdir, fc, cc, arch):
    # move the main source into the source directory
    f1 = os.path.join(srcdir, '..', 'vs2dt3_3.f')
    f1 = os.path.abspath(f1)
    assert os.path.isfile(f1)
    f2 = os.path.join(srcdir, 'vs2dt3_3.f')
    f2 = os.path.abspath(f2)
    shutil.move(f1, f2)
    assert os.path.isfile(f2)

    f1 = open(os.path.join(srcdir, 'vs2dt3_3.f'), 'r')
    f2 = open(os.path.join(srcdir, 'vs2dt3_3.f.tmp'), 'w')
    for line in f1:
        srctxt = "     `POSITION='REWIND')"
        rpctxt = "     `POSITION='REWIND',ACCESS='STREAM')"
        f2.write(line.replace(srctxt, rpctxt))
    f1.close()
    f2.close()
    os.remove(os.path.join(srcdir, 'vs2dt3_3.f'))
    shutil.move(os.path.join(srcdir, 'vs2dt3_3.f.tmp'),
                os.path.join(srcdir, 'vs2dt3_3.f'))

    return
