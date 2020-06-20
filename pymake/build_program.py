import os
import sys
import time
import shutil
import platform
import types
from datetime import datetime

if sys.version_info >= (3, 3):
    from shutil import which
else:
    from distutils.spawn import find_executable as which

from .pymake import main
from .compiler_switches import set_arch, set_compiler, set_debug, \
    set_cflags, set_fflags, set_syslibs
from .download import download_and_unzip, zip_all
from .usgsprograms import usgs_program_data


def get_function_names(module, select_name=None):
    """Get a dictionary of functions available in a user-specified source file.
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
        if isinstance(value, types.FunctionType):
            if select_name is None:
                ladd = True
            else:
                if select_name in value.__name__:
                    ladd = True
            if ladd:
                func[value.__name__] = value
    return func


def set_bindir(target=None):
    """Set path for target based on --travis or --appdir command line
    arguments.

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
    # determine if running on Travis
    is_travis = 'TRAVIS' in os.environ

    # set bindir
    bindir = None
    for idx, arg in enumerate(sys.argv):
        if '--travis' in arg.lower() or is_travis:
            bindir = os.path.join(os.path.expanduser('~'), '.local', 'bin')
            bindir = os.path.abspath(bindir)
        elif '--appdir' in arg.lower():
            bindir = sys.argv[idx + 1]
            if not os.path.isdir(bindir):
                os.mkdir(bindir)

    # set default directory to current directory
    if bindir is None:
        bindir = '.'

    # write message
    if target is not None:
        print('{} will be placed in the directory:\n'.format(target) +
              '    "{}"\n'.format(bindir))

    return bindir


def set_download(download):
    for idx, arg in enumerate(sys.argv):
        if '--nodownload' in arg.lower():
            download = False
    return download


def set_download_clean(download_clean):
    for idx, arg in enumerate(sys.argv):
        if '--nodownload_clean' in arg.lower():
            download_clean = False
    return download_clean


def set_build(target, exe_name):
    """Set boolean that defines whether the target should be built if it
    already exists based on --keep command line argument.

    Parameters
    ----------
    exe_name : str
        executable name that includes double ("dbl"), debug ("d"), and/or
        extension (".exe") based on command line arguments and OS.

    target : str
        target to build

    Returns
    -------
    build : bool

    """
    # determine if running on Travis
    is_travis = 'TRAVIS' in os.environ

    keep = False
    for idx, arg in enumerate(sys.argv):
        if '--keep' in arg.lower() or is_travis:
            keep = True

    build = True
    exe_name = os.path.basename(exe_name)
    if keep:
        print('Determining if {} needs to be built'.format(exe_name))

        bindir = set_bindir()
        if bindir != '.':
            fpth = os.path.join(bindir, exe_name)
            exe_exists = which(fpth)
        else:
            exe_exists = which(exe_name)

        # determine if it is in the current directory
        if exe_exists is None:
            exe_exists = which('./' + exe_name)

        # evaluate if the available version is the same as the
        # source code version
        if exe_exists is not None:
            # check for code.json in exe_pth
            exe_pth = os.path.dirname(exe_exists)

            jpth = 'code.json'
            if jpth in os.listdir(exe_pth):
                fpth = os.path.join(exe_pth, jpth)
                json_dict = usgs_program_data.load_json(fpth=fpth)

                if json_dict is not None:
                    # get current modflow program dictionary
                    prog_dict = usgs_program_data().get_program_dict()

                    # extract the json keys
                    json_keys = list(json_dict.keys())

                    # evaluate if the target is in the json keys
                    if target in json_keys:
                        source_version = prog_dict[target].version
                        existing_version = json_dict[target].version

                        # write a message
                        msg = 'Source code version of {} '.format(target) + \
                              'is "{}"'.format(source_version)
                        print(4 * ' ' + msg)
                        msg = 'Current code version of {} '.format(target) + \
                              'is "{}"\n'.format(existing_version)
                        print(4 * ' ' + msg)

                        prog_version = source_version.split('.')
                        json_version = existing_version.split('.')

                        # evaluate major, minor, etc. version numbers
                        for sp, sj in zip(prog_version, json_version):
                            if int(sp) > int(sj):
                                exe_exists = None
                                break

        if exe_exists is not None:
            build = False
            print('No need to build {}'.format(exe_name) +
                  ' since it exists in the current path')
            print('    "{}"\n'.format(os.path.abspath(exe_exists)))

    return build


def set_extrafiles(target, download_dir):
    """Set extrafiles to compile target. Default is None.

    Parameters
    ----------
    target : str
        target to build

    download_dir : str
        path downloaded files will be placed in

    Returns
    -------
    extra_files : str

    """
    extrafiles = None
    if target in ['zbud6']:
        extrafiles = ['../../../src/Utilities/ArrayHandlers.f90',
                      '../../../src/Utilities/ArrayReaders.f90',
                      '../../../src/Utilities/BlockParser.f90',
                      '../../../src/Utilities/Budget.f90',
                      '../../../src/Utilities/Constants.f90',
                      '../../../src/Utilities/genericutils.f90',
                      '../../../src/Utilities/InputOutput.f90',
                      '../../../src/Utilities/kind.f90',
                      '../../../src/Utilities/OpenSpec.f90',
                      '../../../src/Utilities/sort.f90',
                      '../../../src/Utilities/Message.f90',
                      '../../../src/Utilities/defmacro.fpp',
                      '../../../src/Utilities/Sim.f90',
                      '../../../src/Utilities/SimVariables.f90',
                      '../../../src/Utilities/version.f90']

    # process extrafiles
    if extrafiles:
        prog_dict = usgs_program_data.get_target(target)
        srcdir = os.path.abspath(os.path.join(download_dir,
                                              prog_dict.dirname,
                                              prog_dict.srcdir))
        if isinstance(extrafiles, list):
            for idx, value in enumerate(extrafiles):
                fpth = os.path.join(srcdir, value)
                extrafiles[idx] = os.path.normpath(fpth)
        elif isinstance(extrafiles, str):
            fpth = os.path.join(srcdir, extrafiles)
            extrafiles = os.path.normpath(fpth)
        else:
            msg = 'invalid extrafiles format - must be a list or string'
            raise ValueError(msg)

        # write a message
        msg = 'extra files are being read '
        if isinstance(extrafiles, list):
            msg += 'from a list:\n'
            for value in extrafiles:
                msg += '  {}\n'.format(os.path.relpath(value, download_dir))
        elif isinstance(extrafiles, str):
            msg += 'from a file "{}"\n'.format(os.path.relpath(extrafiles,
                                                               download_dir))
    else:
        msg = 'extra files are not being read'
    print('{}\n'.format(msg))

    return extrafiles


def set_zip():
    """Set file path for zip file.

    Parameters
    ----------

    Returns
    -------
    zip_pth : str
        path for zip file

    """
    zip_pth = None
    for idx, arg in enumerate(sys.argv):
        if arg.lower() == '--zip':
            if idx < len(sys.argv) - 1:
                zip_pth = sys.argv[idx + 1]

    # write c/c++ flags
    if zip_pth is not None:
        msg = 'compiled executibles will be compressed to:\n'
        msg += '    {}\n'.format(zip_pth)
        print(msg)

    return zip_pth


def set_makefile():
    """Set boolean for whether a makefile should be created.

    Parameters
    ----------

    Returns
    -------
    makefile : bool
        boolean indicating if a makefile should be created

    """
    makefile = False
    for idx, arg in enumerate(sys.argv):
        if arg.lower() == '--makefile':
            makefile = True
            break

    # write c/c++ flags
    if makefile:
        msg = 'a GNU make makefile will be created:\n'
        print(msg)

    return makefile


def build_program(target='mf2005', fc='gfortran', cc='gcc', makeclean=True,
                  expedite=False, dryrun=False, double=False, debug=False,
                  include_subdirs=False,
                  fflags=None, cflags=None, syslibs='-lc',
                  arch='intel64', makefile=False,
                  srcdir2=None, extrafiles=None,
                  exe_name=None, exe_dir=None,
                  replace_function=None, verify=True, modify_exe_name=True,
                  download_dir=None, download=True,
                  download_clean=False, download_verify=True, timeout=30):
    """

    Parameters
    ----------
    target : str
        Target USGS program

    fc : str
        fortran compiler

    cc : str
        c/c++ compiler

    makeclean : bool
        Temporary source, object, and module directories will be
        removed after compilation

    expedite : bool
        boolean indicating if only out of date source files will be compiled.
        makeclean must not have been set to True on previous build

    dryrun : bool
        boolean indicating if source files should actually be compiled. Files
        will be deleted, if makeclean is True.

    double : bool
        Create a double precision application

    debug : bool
        Create a double precision application

    include_subdirs : bool
        boolean indicating if subdirectories in srcdir also include
        source files

    fflags : str or list
        user-specified flags for the fortran compiler

    cflags : str or list
        user-specified flags for the c/c++ compiler

    syslibs : str or list
        user-specified syslibs for linking object files

    arch : str
        architecture for windows builds

    makefile : bool
        boolean indicating if a makefile should be created

    srcdir2 : str
        path to a second directory with source code files. Default is None.

    extrafiles : str
        path to a file with defined additional source code files. Default
        is None

    exe_name : str
        user-specified executable file name. If None, target name will
        be used.

    exe_dir : str
        directory where executable should be written

    replace_function : pointer
        pointer to function used to revise source files to compile with
        gfortran, gcc, or g++. If None, source files are not altered.

    verify : bool
        boolean indicating if the existence of the compiled executable
        should be verified after compilation

    modify_exe_name : bool
        boolean indicating if executable name can be altered to include
        identifiers for double and/or debug versions.

    download_dir : str
        directory downloaded files are extracted in

    download : bool
        boolean indicating if the download files should be downloaded.
        Can be overwridden with --nodownload from command line.

    download_clean : bool
        boolean indicating if the downloaded files should be removed
        after the target is built. Can be overwridden with --nodownload_clean
        from command line

    download_verify : bool
        boolean indicating if a verified download will be executed

    timeout : int
        time until the download is considered to timeout

    Returns
    -------
    returncode : int

    """
    # set exe_name
    if exe_name is None:
        exe_name = target

    msg = 'float variable precision: '
    if double:
        msg += '{}'.format('double')
    else:
        msg += '{}'.format('single')
    print(msg)

    if modify_exe_name:
        if double:
            filename, file_extension = os.path.splitext(exe_name)
            if 'dbl' not in filename.lower():
                exe_name = filename + 'dbl' + file_extension
        if debug:
            filename, file_extension = os.path.splitext(exe_name)
            if filename.lower()[-1] != 'd':
                exe_name = filename + 'd' + file_extension

    # if a user-defined replace_function has not been provided then
    # use the standard replace function, if one is available
    if replace_function is None:
        replace_function = build_replace(target)

    if platform.system().lower() == 'windows':
        filename, file_extension = os.path.splitext(exe_name)
        if file_extension.lower() != '.exe':
            exe_name += '.exe'

    # determine if the target should be built
    build = set_build(target, exe_name)

    returncode = 0
    if build:
        if exe_dir is not None:
            exe_name = os.path.abspath(os.path.join(exe_dir, exe_name))

        # extract program data for target
        prog_dict = usgs_program_data.get_target(target)

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

        # Download the distribution (can be overridden with --nodownload)
        download = set_download(download)
        if download:
            download_and_unzip(url, pth=download_dir, verify=download_verify,
                               timeout=timeout)

        if replace_function is not None:
            print('replacing select source files for {}\n'.format(target))
            replace_function(srcdir, fc, cc, arch, double)

        # compile code
        print('compiling...{}'.format(os.path.relpath(exe_name)))
        returncode = main(srcdir, exe_name, fc=fc, cc=cc, makeclean=makeclean,
                          expedite=expedite, dryrun=dryrun,
                          double=double, debug=debug,
                          include_subdirs=include_subdirs,
                          fflags=fflags, cflags=cflags, syslibs=syslibs,
                          arch=arch, makefile=makefile, srcdir2=srcdir2,
                          extrafiles=extrafiles)

        app = os.path.relpath(exe_name)
        msg = 'failure to build {}.'.format(app)
        assert returncode == 0, msg

        if verify and not dryrun:
            msg = '{} build failure.'.format(app)
            assert os.path.isfile(exe_name), msg

        # remove *.exp and *.lib from windows builds
        if target in ['gsflow', 'mfnwt']:
            if fc == 'ifort':
                if 'win32' in sys.platform.lower():
                    fpth = exe_name.replace('.exe', '.exp')
                    if os.path.exists(fpth):
                        os.remove(fpth)
                    fpth = exe_name.replace('.exe', '.lib')
                    if os.path.exists(fpth):
                        os.remove(fpth)

        # clean download directory if different than directory with executable
        download_clean = set_download_clean(download_clean)
        if download_clean:
            edir = os.path.abspath(os.path.dirname(exe_name))
            ddir = os.path.abspath(download_dir)
            if edir != ddir:
                if os.path.isdir(ddir):
                    msg = 'deleting {}'.format(ddir)
                    print(msg)
                    ntries = 10
                    for itries in range(ntries):
                        msg = '    removal attempt {:>2d} '.format(itries + 1)
                        msg += 'of {:>2d}'.format(ntries)
                        print(msg)

                        # wait to delete on windows
                        if platform.system().lower() == 'windows':
                            time.sleep(3)

                        # remove the directory
                        try:
                            shutil.rmtree(ddir)
                            break
                        except:
                            pass

                    print('\n')

                    # wait prior to returning on windows
                    if platform.system().lower() == 'windows':
                        time.sleep(6)

    return returncode


def build_targets(current=True):
    """Build a list of targets.

    Parameters
    ----------
    current : bool
        return list of current targets. If current is False, returned list
        will include all available USGS applications included in usgsprograms.txt.
        Default is True

    Returns
    -------
    targets : list
        list of targets

    """
    return usgs_program_data.get_keys(current=current)


def build_replace(targets):
    """Get pointers to appropriate replace_function for a target.

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
    """Build all of the current targets or a subset of targets.

    Parameters
    ----------
    targets : str or list of str
        targets to build. If targets is None, all current targets will
        be build. Default is None

    Returns
    -------
    returncode : int

    """
    start_time = datetime.now()
    if targets is None:
        targets = build_targets()
    else:
        if isinstance(targets, str):
            targets = [targets]

    code_dict = {}

    for idt, target in enumerate(targets):
        start_downcomp = datetime.now()

        code_dict[target] = usgs_program_data.get_target(target)

        # write system information
        print('{} will be built '.format(target) +
              'for the "{}" operating system\n'.format(sys.platform))

        # set bindir
        bindir = set_bindir(target)

        # set double precision flag and whether the executable name
        # can be modified
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
        fflags = set_fflags(target, fc)

        # set c/c++ flags
        cflags = set_cflags(target, cc)

        # set linker syslibs
        syslibs = set_syslibs(target, fc, cc)

        # set architecture
        arch = set_arch(target)

        # set include_subdirs
        if target in ['mf6', 'gridgen', 'mf6beta', 'gsflow']:
            include_subdirs = True
        else:
            include_subdirs = False

        # set replace function
        replace_function = build_replace(target)

        # set download information
        download_now = True
        download_clean = True
        download_dir = 'temp'

        # modify download if mf6 and also building zonbud6
        if target == 'mf6':
            if idt + 1 < len(targets):
                if targets[idt + 1] == 'zbud6':
                    download_clean = False
        elif target == 'zbud6':
            if idt > 0:
                if targets[idt - 1] == 'mf6':
                    download_now = False

        # modify download if mfusg and also building zonbudusg
        if target == 'mfusg':
            if idt + 1 < len(targets):
                if targets[idt + 1] == 'zonbudusg':
                    download_clean = False
        elif target == 'zonbudusg':
            if idt > 0:
                if targets[idt - 1] == 'mfusg':
                    download_now = False

        if target in ['mt3dms', 'triangle', 'mf6beta']:
            download_verify = False
            timeout = 10
        else:
            download_verify = True
            timeout = 30

        # set extrafiles
        extrafiles = set_extrafiles(target, download_dir)

        # determine the
        precision = usgs_program_data.get_precision(target)

        for idx, double in enumerate(precision):
            # set clean flag
            if len(precision) > 1:
                if idx == 0:
                    download = download_now
                else:
                    download = False
                if idx < len(precision) - 1:
                    clean = False
                else:
                    clean = download_clean
            else:
                download = download_now
                clean = download_clean

            # set makefile, only done for first target and precision
            makefile = False
            if idt == 0 and idx == 0:
                makefile = set_makefile()

            # print download information
            msg = 'downloading file:         {}\n'.format(download)
            msg += 'verified download:        {}\n'.format(download_verify)
            msg += 'download timeout:         {} sec.\n'.format(timeout)
            msg += 'create GNU make makefile: {}\n'.format(makefile)
            msg += 'cleaning extracted files: {}\n'.format(clean)
            print(msg)

            # build the code
            returncode = build_program(target=target,
                                       fc=fc,
                                       cc=cc,
                                       double=double,
                                       debug=debug,
                                       fflags=fflags,
                                       cflags=cflags,
                                       syslibs=syslibs,
                                       arch=arch,
                                       include_subdirs=include_subdirs,
                                       extrafiles=extrafiles,
                                       replace_function=replace_function,
                                       modify_exe_name=modify_exe_name,
                                       exe_dir=bindir,
                                       download=download,
                                       download_dir=download_dir,
                                       download_clean=clean,
                                       download_verify=download_verify,
                                       timeout=timeout,
                                       makefile=makefile)

        # calculate download and compile time
        end_downcomp = datetime.now()
        elapsed = end_downcomp - start_downcomp
        print('elapsed download and compile time (hh:mm:ss.ms): ' +
              '{}\n'.format(elapsed))

    end_time = datetime.now()
    elapsed = end_time - start_time
    print('elapsed time (hh:mm:ss.ms): {}\n'.format(elapsed))

    return returncode


def compress_apps(targets=None):
    """

    Parameters
    ----------
    targets : str or list of str

    Returns
    -------
    returncode : int

    """
    # intialize the return code
    returncode = 0

    # get the specified zip file path
    zip_pth = set_zip()

    # compress the compiled executables
    if zip_pth is not None:
        # determine targets if not defined
        if targets is None:
            targets = build_targets()

        # add code.json
        if 'code.json' not in targets:
            targets.append('code.json')

        # delete the zip file if it exists
        if os.path.exists(zip_pth):
            print("Deleting existing zipfile '{}'".format(zip_pth))
            os.remove(zip_pth)

        # set the bin dir
        bindir = set_bindir()

        # compress the compiled executables
        msg = "Compressing files in '{}' ".format(bindir) + \
              "directory to zip file '{}'".format(zip_pth)
        print(msg)
        success = zip_all(zip_pth, dir_pths=bindir, patterns=targets)

        # set return code
        if not success:
            returncode = 1

    return returncode


# routines for updating source files locations and to compile
# with gfortran, gcc, and g++
def update_triangle_files(srcdir, fc, cc, arch, double):
    """Update the triangle source files.

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
    prog_dict = usgs_program_data().get_target('triangle')
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


def update_mt3dms_files(srcdir, fc, cc, arch, double):
    """Update the MT3D source files.

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
    prog_dict = usgs_program_data().get_target('mt3dms')
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
            shutil.move(src_file, dst_file)

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

    for file_list in ['mt_btn5.for', 'mt_utl5.for']:
        fpth = os.path.join(srcdir, file_list)
        with open(fpth) as f:
            lines = f.readlines()
        f = open(fpth, 'w')
        for line in lines:
            if "'FILESPEC.INC'" in line:
                line = line.replace("'FILESPEC.INC'",
                                    "'filespec.inc'")
            f.write(line)
        f.close()

    return


def update_swtv4_files(srcdir, fc, cc, arch, double):
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
        if 'linux' in sys.platform.lower() or 'darwin' in sys.platform.lower():
            os.rename(src, dst)

    if 'linux' in sys.platform.lower() or 'darwin' in sys.platform.lower():
        updfile = False
        if cc in ['icc', 'clang', 'gcc']:
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


def update_mf2005_files(srcdir, fc, cc, arch, double):
    # update utl7.f
    tag = 'IBINARY=0'
    fpth = os.path.join(srcdir, 'utl7.f')
    with open(fpth) as f:
        lines = f.readlines()
    f = open(fpth, 'w')
    for line in lines:
        if tag in line:
            indent = len(line) - len(line.lstrip())
            line += indent * ' ' + 'JAUX=0\n'
        f.write(line)
    f.close()

    # update gwf2swi27.f
    tag = 'INTEGER, PARAMETER :: VERSIZE ='
    prec = 4
    if double:
        prec = 8
    fpth = os.path.join(srcdir, 'gwf2swi27.f')
    with open(fpth) as f:
        lines = f.readlines()
    f = open(fpth, 'w')
    for line in lines:
        if line.lower()[0] not in ['!', 'c']:
            if tag in line:
                indent = len(line) - len(line.lstrip())
                line = indent * ' ' + tag + ' {}\n'.format(prec)
        f.write(line)
    f.close()

    # update gwf2swt7.f
    tag = 'EST(J,I,N)=0.0'
    fpth = os.path.join(srcdir, 'gwf2swt7.f')
    with open(fpth) as f:
        lines = f.readlines()
    f = open(fpth, 'w')
    for line in lines:
        if tag in line:
            indent = len(line) - len(line.lstrip())
            line += indent * ' ' + 'PCS(J,I,N)=0.0\n'
        f.write(line)
    f.close()


def update_mfnwt_files(srcdir, fc, cc, arch, double):
    # update utl7.f
    fpth = os.path.join(srcdir, 'utl7.f')
    tag = 'IBINARY=0'
    with open(fpth) as f:
        lines = f.readlines()
    f = open(fpth, 'w')
    for line in lines:
        if tag in line:
            indent = len(line) - len(line.lstrip())
            line += indent * ' ' + 'JAUX=0\n'
        f.write(line)
    f.close()

    # update gwf2swt7.f
    tag = 'EST(J,I,N)=0.0'
    fpth = os.path.join(srcdir, 'gwf2swt7.f')
    if os.path.exists(fpth):
        with open(fpth) as f:
            lines = f.readlines()
        f = open(fpth, 'w')
        for line in lines:
            if tag in line:
                indent = len(line) - len(line.lstrip())
                line += indent * ' ' + 'PCS(J,I,N)=0.0\n'
            f.write(line)
        f.close()

    # remove lrestart.f
    fpth = os.path.join(srcdir, 'Irestart.f')
    if os.path.exists(fpth):
        os.remove(fpth)

    # update gwf2swi27.f or gwf2swi27.f
    fpth = os.path.join(srcdir, 'gwf2swi27.f')
    if not os.path.exists(fpth):
        fpth = os.path.join(srcdir, 'gwf2swi27.fpp')
    if os.path.exists(fpth):
        tag = '(i,csolver(i),i=1,3)'
        new_tag = '(i,csolver(i),i=1,2)'
        with open(fpth) as f:
            lines = f.readlines()
        f = open(fpth, 'w')
        for line in lines:
            if tag in line:
                line = line.replace(tag, new_tag)
            f.write(line)
        f.close()


def update_gsflow_files(srcdir, fc, cc, arch, double):
    # update gwf2swt7.f
    tag = 'EST(J,I,N)=0.0'
    fpth = os.path.join(srcdir, 'modflow', 'gwf2swt7.f')
    with open(fpth) as f:
        lines = f.readlines()
    f = open(fpth, 'w')
    for line in lines:
        if tag in line:
            indent = len(line) - len(line.lstrip())
            line += indent * ' ' + 'PCS(J,I,N)=0.0\n'
        f.write(line)
    f.close()

    # update gwf2swi27.f or gwf2swi27.fpp
    fpth = os.path.join(srcdir, 'modflow', 'gwf2swi27.f')
    if not os.path.exists(fpth):
        fpth = os.path.join(srcdir, 'modflow', 'gwf2swi27.fpp')
    if os.path.exists(fpth):
        tag = '(i,csolver(i),i=1,3)'
        new_tag = '(i,csolver(i),i=1,2)'
        with open(fpth) as f:
            lines = f.readlines()
        f = open(fpth, 'w')
        for line in lines:
            if tag in line:
                line = line.replace(tag, new_tag)
            f.write(line)
        f.close()

    # remove merge and lib directories
    pths = [os.path.join(srcdir, 'merge'), os.path.join(srcdir, 'lib')]
    for pth in pths:
        if os.path.isdir(pth):
            shutil.rmtree(pth)

    # remove existing *.mod, *.o, and *.a (if any are left) files
    dpths = [os.path.join(srcdir, o) for o in os.listdir(srcdir)
             if os.path.isdir(os.path.join(srcdir, o))]

    for dpth in dpths:
        for f in os.listdir(dpth):
            ext = os.path.splitext(f)[1]
            fpth = os.path.join(dpth, f)
            if ext in ['.mod', '.o', '.a']:
                os.remove(fpth)

    # edit and remove os specific files
    if sys.platform.lower() == 'win32':
        if 'ifort' not in fc:
            tag = "FORM='BINARY'"
            new_tag = "FORM='UNFORMATTED', ACCESS='STREAM'"
            fpth = os.path.join(srcdir, 'prms', 'utils_prms_windows.f90')
            with open(fpth) as f:
                lines = f.readlines()
            f = open(fpth, 'w')
            for line in lines:
                if tag in line:
                    line = line.replace(tag, new_tag)
                f.write(line)
            f.close()

        fpths = [os.path.join(srcdir, 'prms', 'utils_prms_linux.f90'),
                 os.path.join(srcdir, 'prms', 'utils_prms.f90')]
    else:
        fpths = [os.path.join(srcdir, 'prms', 'utils_prms_linux.f90'),
                 os.path.join(srcdir, 'prms', 'utils_prms_windows.f90')]
    for fpth in fpths:
        os.remove(fpth)

    return


def update_mf2000_files(srcdir, fc, cc, arch, double):
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
        shutil.move(os.path.join(tpth, f), os.path.join(srcdir, f))
    tpth = os.path.join(srcdir, 'mf2k', 'serial')
    files = [f for f in os.listdir(tpth) if
             os.path.isfile(os.path.join(tpth, f))]
    for f in files:
        shutil.move(os.path.join(tpth, f), os.path.join(srcdir, f))

    # Remove mf2k directory in source directory
    tpth = os.path.join(srcdir, 'mf2k')
    shutil.rmtree(tpth)

    # modify the openspec.inc file to use binary instead of unformatted
    fname = os.path.join(srcdir, 'openspec.inc')
    with open(fname) as f:
        lines = f.readlines()
    with open(fname, 'w') as f:
        for line in lines:
            if "      DATA FORM/'UNFORMATTED'/" in line:
                line = "C     DATA FORM/'UNFORMATTED'/\n"
            if "C      DATA FORM/'BINARY'/" in line:
                line = "       DATA FORM/'BINARY'/\n"
            f.write(line)
    return


def update_mflgr_files(srcdir, fc, cc, arch, double):
    # update gwf2swt7.f
    tag = 'EST(J,I,N)=0.0'
    fpth = os.path.join(srcdir, 'gwf2swt7.f')
    with open(fpth) as f:
        lines = f.readlines()
    f = open(fpth, 'w')
    for line in lines:
        if tag in line:
            indent = len(line) - len(line.lstrip())
            line += indent * ' ' + 'PCS(J,I,N)=0.0\n'
        f.write(line)
    f.close()


def update_mp6_files(srcdir, fc, cc, arch, double):
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


def update_mp7_files(srcdir, fc, cc, arch, double):
    fpth = os.path.join(srcdir, 'StartingLocationReader.f90')
    with open(fpth) as f:
        lines = f.readlines()
    f = open(fpth, 'w')
    for line in lines:
        if 'pGroup%Particles(n)%InitialFace = 0' in line:
            continue
        f.write(line)
    f.close()


def update_vs2dt_files(srcdir, fc, cc, arch, double):
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
