"""Main pymake function, :code:`pymake.main()`, that is called when pymake is
run from the command line. :code:`pymake.main()` can also be called directly
from a script in combination with :code:`pymake.parser()`.

.. code-block:: python

    import pymake
    args = pymake.parser()
    pymake.main(
        args.srcdir,
        args.target,
        fc=args.fc,
        cc=args.cc,
        makeclean=args.makeclean,
        expedite=args.expedite,
        dryrun=args.dryrun,
        double=args.double,
        debug=args.debug,
        include_subdirs=args.subdirs,
        fflags=args.fflags,
        cflags=args.cflags,
        arch=args.arch,
        syslibs=args.syslibs,
        makefile=args.makefile,
        srcdir2=args.commonsrc,
        extrafiles=args.extrafiles,
        excludefiles=args.excludefiles,
        sharedobject=args.sharedobject,
        appdir=args.appdir,
        verbose=args.verbose,
        inplace=args.inplace,
    )


The script could be run from the command line using:

.. code-block:: bash

    python myscript.py ../src myapp -fc=ifort -cc=icc

"""
import os
import traceback
import shutil
import datetime
import inspect

from .config import __version__
from .utils._Popen_wrapper import (
    _process_Popen_initialize,
    _process_Popen_command,
    _process_Popen_stdout,
    _process_Popen_communicate,
)
from .utils._compiler_switches import (
    _get_osname,
    _get_optlevel,
    _get_c_flags,
    _get_fortran_flags,
    _get_linker_flags,
    _get_os_macro,
)
from .utils._compiler_language_files import (
    _get_srcfiles,
    _get_ordered_srcfiles,
    _get_c_files,
    _get_fortran_files,
    _preprocess_file,
)

# define temporary directories
objdir_temp = os.path.join(".", "obj_temp")
moddir_temp = os.path.join(".", "mod_temp")


def main(
    srcdir=None,
    target=None,
    fc="gfortran",
    cc="gcc",
    makeclean=True,
    expedite=False,
    dryrun=False,
    double=False,
    debug=False,
    include_subdirs=False,
    fflags=None,
    cflags=None,
    syslibs=None,
    arch="intel64",
    makefile=False,
    srcdir2=None,
    extrafiles=None,
    excludefiles=None,
    sharedobject=False,
    appdir=None,
    verbose=False,
    inplace=False,
    networkx=False,
):
    """Main pymake function.

    Parameters
    ----------
    srcdir : str
        path for directory containing source files
    target : str
        executable name or path for executable to create
    fc : str
        fortran compiler
    cc : str
        c or cpp compiler
    makeclean : bool
        boolean indicating if intermediate files should be cleaned up
        after successful build
    expedite : bool
        boolean indicating if only out of date source files will be compiled.
        Clean must not have been used on previous build.
    dryrun : bool
        boolean indicating if source files should be compiled.  Files will be
        deleted, if makeclean is True.
    double : bool
        boolean indicating a compiler switch will be used to create an
        executable with double precision real variables.
    debug : bool
        boolean indicating is a debug executable will be built
    include_subdirs : bool
        boolean indicating source files in srcdir subdirectories should be
        included in the build
    fflags : list
        user provided list of fortran compiler flags
    cflags : list
        user provided list of c or cpp compiler flags
    syslibs : list
        user provided syslibs
    arch : str
        Architecture to use for Intel Compilers on Windows (default is intel64)
    makefile : bool
        boolean indicating if a GNU make makefile should be created
    srcdir2 : str
        additional directory with common source files.
    extrafiles : str
        path for extrafiles file that contains paths to additional source
        files to include
    excludefiles : str
        path for excludefiles file that contains filename of source files
        to exclude from the build
    sharedobject : bool
        boolean indicating a shared object will be built
    appdir : str
        path for executable
    verbose : bool
        boolean indicating if output will be printed to the terminal
    inplace : bool
        boolean indicating that the source files in srcdir, srcdir2, and
        defined in extrafiles will be used directly. If inplace is True,
        source files will be copied to a directory named srcdir_temp.
        (default is False)
    networkx : bool
        boolean indicating that the NetworkX python package will be used to
        create the Directed Acyclic Graph (DAG) used to determine the order
        source files are compiled in. The NetworkX package tends to result in
        a unique DAG more often than the standard algorithm used in pymake.
        (default is False)

    Returns
    -------
    returncode : int
        return code

    """

    if srcdir is not None and target is not None:

        if inplace:
            srcdir_temp = srcdir
        else:
            srcdir_temp = os.path.join(".", "src_temp")

        # process appdir
        if appdir is not None:
            target = os.path.join(appdir, target)

            # make appdir if it does not exist
            if not os.path.isdir(appdir):
                os.makedirs(appdir)
        else:
            target = os.path.join(".", target)

        # set fc and cc to None if they are passed as 'none'
        if fc == "none":
            fc = None
        if cc == "none":
            cc = None
        if fc is None and cc is None:
            msg = (
                "Nothing to do the fortran (-fc) and c/c++ compilers (-cc)"
                + "are both 'none'."
            )
            raise ValueError(msg)

        # convert fflags, cflags, and syslibs to lists
        if fflags is None:
            fflags = []
        elif isinstance(fflags, str):
            fflags = fflags.split()
        if cflags is None:
            cflags = []
        elif isinstance(cflags, str):
            cflags = cflags.split()
        if syslibs is None:
            syslibs = []
        elif isinstance(syslibs, str):
            syslibs = syslibs.split()

        # write summary information
        if verbose:
            print("\nsource files are in:\n    {}\n".format(srcdir))
            print("executable name to be created:\n    {}\n".format(target))
            if srcdir2 is not None:
                msg = "additional source files are in:\n" + "     {}\n".format(
                    srcdir2
                )
                print(msg)

        # make sure the path for the target exists
        pth = os.path.dirname(target)
        if pth == "":
            pth = "."
        if not os.path.exists(pth):
            print("creating target path - {}\n".format(pth))
            os.makedirs(pth)

        # initialize
        srcfiles = _pymake_initialize(
            srcdir,
            target,
            srcdir2,
            extrafiles,
            excludefiles,
            include_subdirs,
            srcdir_temp,
        )

        # get ordered list of files to compile
        srcfiles = _get_ordered_srcfiles(srcfiles, networkx)

        # set intelwin flag to True in compiling on windows with Intel compilers
        intelwin = False
        if _get_osname() == "win32":
            if fc is not None:
                if fc in ["ifort", "mpiifort"]:
                    intelwin = True
            if cc is not None:
                if cc in ["cl", "icl"]:
                    intelwin = True

        # update openspec files based on intelwin
        if not intelwin:
            _create_openspec(srcfiles, verbose)

        # compile the executable
        returncode = _pymake_compile(
            srcfiles,
            target,
            fc,
            cc,
            expedite,
            dryrun,
            double,
            debug,
            fflags,
            cflags,
            syslibs,
            arch,
            intelwin,
            sharedobject,
            verbose,
        )

        # create makefile
        if makefile:
            _create_makefile(
                target,
                srcdir,
                srcdir2,
                extrafiles,
                srcfiles,
                debug,
                double,
                fc,
                cc,
                fflags,
                cflags,
                syslibs,
                verbose,
            )

        # clean up temporary files
        if makeclean and returncode == 0:
            _clean_temp_files(target, intelwin, inplace, srcdir_temp, verbose)
    else:
        msg = (
            "Nothing to do, the srcdir ({}) ".format(srcdir)
            + "and/or target ({}) ".format(target)
            + "are not specified."
        )
        raise ValueError(msg)

    return returncode


def _pymake_initialize(
    srcdir,
    target,
    commonsrc,
    extrafiles,
    excludefiles,
    include_subdirs,
    srcdir_temp,
):
    """Remove temp source directory and target, and then copy source into
    source temp directory.

    Parameters
    ----------
    srcdir : str
        path for directory containing source files
    target : str
        path for executable to create
    commonsrc : str
        additional directory with common source files.
    extrafiles : str
        path for extrafiles file that contains paths to additional source
        files to include
    excludefiles : str
        path for excludefiles file that contains filename of source files
        to exclude from the build
    include_subdirs : bool
        boolean indicating source files in srcdir subdirectories should be
        included in the build
    srcdir_temp : str
        path for directory that will contain the source files. If
        srcdir_temp is the same as srcdir then the original source files
        will be used.

    Returns
    -------
    srcfiles : list
        list of source files for build

    """
    # remove the target if it already exists
    if os.path.isfile(target):
        os.remove(target)

    inplace = False
    if srcdir == srcdir_temp:
        inplace = True

    # if exclude is not None, then it is a text file with a list of
    # source files that need to be excluded from srctemp.
    excludefiles = _get_extra_exclude_files(excludefiles)
    if excludefiles:
        for idx, exclude_file in enumerate(excludefiles):
            excludefiles[idx] = os.path.basename(exclude_file)

    # remove srcdir_temp and copy in srcdir
    if not inplace:
        if os.path.isdir(srcdir_temp):
            shutil.rmtree(srcdir_temp)
        if excludefiles:
            shutil.copytree(
                srcdir,
                srcdir_temp,
                ignore=shutil.ignore_patterns(*excludefiles),
            )
        else:
            shutil.copytree(srcdir, srcdir_temp)

    # get a list of source files in srcdir_temp to include
    srcfiles = _get_srcfiles(srcdir_temp, include_subdirs)

    # copy files from a specified common source directory if
    # commonsrc is not None
    if commonsrc is not None:
        if not inplace:
            src = os.path.relpath(commonsrc, os.getcwd())
            dst = os.path.join(
                srcdir_temp, os.path.basename(os.path.normpath(commonsrc))
            )
            if excludefiles:
                shutil.copytree(
                    src,
                    dst,
                    ignore=shutil.ignore_patterns(*excludefiles),
                )
            else:
                shutil.copytree(src, dst)
        else:
            dst = os.path.normpath(os.path.relpath(commonsrc, srcdir_temp))

        srcfiles += _get_srcfiles(dst, include_subdirs)

    # if extrafiles is not None, then it is a text file with a list of
    # additional source files that need to be copied into srctemp and
    # compiled.
    files = _get_extra_exclude_files(extrafiles)
    if files is None:
        files = []
    for fpth in files:
        if not os.path.isfile(fpth):
            # check if fpp file has been replaced by a free format file
            if fpth.endswith(".fpp"):
                fpth2 = fpth.replace(".fpp", ".f90")
                if os.path.isfile(fpth):
                    fpth = fpth2
                else:
                    msg = "Current working directory: {}\n".format(os.getcwd())
                    msg += "Error in extrafiles: {}\n".format(extrafiles)
                    msg += "Could not find file: {}".format(fpth)
                    raise FileNotFoundError(msg)
        if inplace:
            dst = os.path.normpath(os.path.relpath(fpth, os.getcwd()))
        else:
            dst = os.path.join(srcdir_temp, os.path.basename(fpth))
            if os.path.isfile(dst):
                raise ValueError(
                    "Error with extrafile.  Name conflicts with "
                    "an existing source file: {}".format(dst)
                )
        if not inplace:
            shutil.copy(fpth, dst)

        # add extrafiles to srcfiles
        srcfiles.append(dst)

    # remove exclude files from srcfiles list
    if excludefiles:
        remove_list = []
        for fpth in srcfiles:
            if os.path.basename(fpth) in excludefiles:
                remove_list.append(fpth)
        for fpth in remove_list:
            srcfiles.remove(fpth)

    # if they don't exist, create directories for objects and mods
    if not os.path.exists(objdir_temp):
        os.makedirs(objdir_temp)
    if not os.path.exists(moddir_temp):
        os.makedirs(moddir_temp)

    return srcfiles


def _get_extra_exclude_files(extrafiles):
    """Get extrafiles to include in compilation from a file or a list.

    Parameters
    ----------
    extrafiles : str
        path for extrafiles file that contains paths to additional source
        files to include

    Returns
    -------
    files : list
        list of files in the extra files input file

    """
    if extrafiles is None:
        files = None
    else:
        if isinstance(extrafiles, list):
            files = extrafiles
        elif os.path.isfile(extrafiles):
            efpth = os.path.dirname(extrafiles)
            with open(extrafiles, "r") as f:
                files = []
                for line in f:
                    fname = line.strip().replace("\\", "/")
                    if len(fname) > 0:
                        fname = os.path.abspath(os.path.join(efpth, fname))
                        files.append(fname)
        else:
            raise Exception(
                "extrafiles must be either a list of files "
                "or the name of a text file that contains a list "
                "of files."
            )
    return files


def _clean_temp_files(target, intelwin, inplace, srcdir_temp, verbose=False):
    """Cleanup intermediate files. Remove mod and object files, and remove the
    temporary source directory.

    Parameters
    ----------
    target : str
        path for executable to create
    intelwin : bool
        boolean indicating if pymake was used to compile source code on
        Windows using Intel compilers
    inplace : bool
        boolean indicating that the source files in srcdir, srcdir2, and
        defined in extrafiles will be used directly. If inplace is True,
        source files will be copied to a directory named srcdir_temp.
        (default is False)
    srcdir_temp : str
        path for directory that will contain the source files. If
        srcdir_temp is the same as srcdir then the original source files
        will be used.
    verbose : bool
        boolean indicating if output will be printed to the terminal

    Returns
    -------
    None

    """
    # set object extension
    if intelwin:
        objext = ".obj"
    else:
        objext = ".o"

    # clean things up
    if verbose:
        print("\nCleaning up temporary source, object, and module files...")
    filelist = os.listdir(".")
    delext = [".mod", objext]
    for f in filelist:
        for ext in delext:
            if f.endswith(ext):
                if verbose:
                    print("    removing...{}".format(f))
                os.remove(f)

    # shared object intermediate files
    if verbose:
        print("\nCleaning up intermediate shared object files...")
    delext = [".exp", ".lib"]
    dpth = os.path.dirname(os.path.abspath(target))
    for f in os.listdir(dpth):
        fpth = os.path.join(dpth, f)
        for ext in delext:
            if fpth.endswith(ext):
                if verbose:
                    print("    removing...'{}'".format(fpth))
                os.remove(fpth)

    # remove temporary directories
    if verbose:
        msg = (
            "\nCleaning up temporary source, object, "
            + "and module directories..."
        )
        print(msg)
    if not inplace:
        if os.path.isdir(srcdir_temp):
            if verbose:
                print("removing...'{}'".format(srcdir_temp))
            shutil.rmtree(srcdir_temp)
    if os.path.isdir(objdir_temp):
        if verbose:
            print("removing...'{}'".format(objdir_temp))
        shutil.rmtree(objdir_temp)
    if os.path.isdir(moddir_temp):
        if verbose:
            print("removing...'{}'".format(moddir_temp))
        shutil.rmtree(moddir_temp)

    # remove the windows batchfile
    if intelwin:
        os.remove("compile.bat")
    return


def _create_openspec(srcfiles, verbose):
    """Create new openspec.inc, FILESPEC.INC, and filespec.inc files that uses
    STREAM ACCESS. This is specific to MODFLOW and MT3D based targets. Source
    directories are scanned and files defining file access are replaced.

    Parameters
    ----------

    Returns
    -------
    None

    """
    # list of files to replace
    files = ["openspec.inc", "filespec.inc"]

    # build list of directory paths from srcfiles
    dpths = []
    for fpth in srcfiles:
        dpth = os.path.dirname(fpth)
        if dpth not in dpths:
            dpths.append(dpth)

    # replace files in directory paths if they exist
    for dpth in dpths:
        for file in files:
            fpth = os.path.join(dpth, file)
            if os.path.isfile(fpth):
                if verbose:
                    print('replacing..."{}"'.format(fpth))
                f = open(fpth, "w")
                line = (
                    "c -- created by pymake_base.py\n"
                    + "      CHARACTER*20 ACCESS,FORM,ACTION(2)\n"
                    + "      DATA ACCESS/'STREAM'/\n"
                    + "      DATA FORM/'UNFORMATTED'/\n"
                    + "      DATA (ACTION(I),I=1,2)/'READ','READWRITE'/\n"
                    + "c -- end of include file\n"
                )
                f.write(line)
                f.close()
    return


def _check_out_of_date(srcfile, objfile):
    """Check if existing object files are current with the existing source
    files.

    Parameters
    ----------
    srcfile : str
        source file path
    objfile : str
        object file path

    Returns
    -------
    stale : bool
        boolean indicating if the object file is current

    """
    stale = True
    if os.path.exists(objfile):
        t1 = os.path.getmtime(objfile)
        t2 = os.path.getmtime(srcfile)
        if t1 > t2:
            stale = False
    return stale


def _pymake_compile(
    srcfiles,
    target,
    fc,
    cc,
    expedite,
    dryrun,
    double,
    debug,
    fflags,
    cflags,
    syslibs,
    arch,
    intelwin,
    sharedobject,
    verbose,
):
    """Standard compile method.

    Parameters
    -------
    srcfiles : list
        list of source file names
    target : str
        path for executable to create
    fc : str
        fortran compiler
    cc : str
        c or cpp compiler
    expedite : bool
        boolean indicating if only out of date source files will be compiled.
        Clean must not have been used on previous build.
    dryrun : bool
        boolean indicating if source files should be compiled.  Files will be
        deleted, if makeclean is True.
    double : bool
        boolean indicating a compiler switch will be used to create an
        executable with double precision real variables.
    debug : bool
        boolean indicating is a debug executable will be built
    fflags : list
        user provided list of fortran compiler flags
    cflags : list
        user provided list of c or cpp compiler flags
    syslibs : list
        user provided syslibs
    arch : str
        architecture to use for Intel Compilers on Windows (default is intel64)
    intelwin : bool
        boolean indicating if pymake was used to compile source code on
        Windows using Intel compilers
    sharedobject : bool
        boolean indicating a shared object will be built
    verbose : bool
        boolean indicating if output will be printed to the terminal
    inplace : bool
        boolean indicating that the source files in srcdir, srcdir2, and
        defined in extrafiles will be used directly. If inplace is True,
        source files will be copied to a directory named srcdir_temp.
        (default is False)

    Returns
    -------
    returncode : int
        returncode

    """
    # write pymake setting
    if verbose:
        msg = (
            "\nPymake settings in {}\n".format(_pymake_compile.__name__)
            + 40 * "-"
        )
        print(msg)
        frame = inspect.currentframe()
        fnargs, _, _, values = inspect.getargvalues(frame)
        for arg in fnargs:
            value = values[arg]
            if not value:
                value = "None"
            elif isinstance(value, list):
                value = ", ".join(value)
            print(" {}={}".format(arg, value))

    # initialize returncode
    returncode = 0

    # initialize ilink
    ilink = 0

    # set optimization levels
    optlevel = _get_optlevel(
        target, fc, cc, debug, fflags, cflags, verbose=verbose
    )

    # get fortran and c compiler switches
    tfflags = _get_fortran_flags(
        target,
        fc,
        fflags,
        debug,
        double,
        sharedobject=sharedobject,
        verbose=verbose,
    )
    tcflags = _get_c_flags(
        target,
        cc,
        cflags,
        debug,
        srcfiles,
        sharedobject=sharedobject,
        verbose=verbose,
    )

    # get linker flags and syslibs
    lc, tlflags = _get_linker_flags(
        target,
        fc,
        cc,
        syslibs,
        srcfiles,
        sharedobject=sharedobject,
        verbose=verbose,
    )

    # clean exe prior to build so that test for exe below can return a
    # non-zero error code
    if os.path.isfile(target):
        if verbose:
            msg = "removing existing target with same name: {}".format(target)
            print(msg)
        os.remove(target)

    if intelwin:
        # update compiler names if necessary
        ext = ".exe"
        if fc is not None:
            if ext not in fc:
                fc += ext
        if cc is not None:
            if ext not in cc:
                cc += ext
        if ext not in lc:
            lc += ext

        # update target extension
        if sharedobject:
            program_path, ext = os.path.splitext(target)
            if ext.lower() != ".dll":
                target = program_path + ".dll"
        else:
            if ext not in target:
                target += ext

        # delete the batch file if it exists
        batchfile = "compile.bat"
        if os.path.isfile(batchfile):
            try:
                os.remove(batchfile)
            except:
                if verbose:
                    print("could not remove '{}'".format(batchfile))

        # Create target using a batch file on Windows
        try:
            _create_win_batch(
                batchfile,
                fc,
                cc,
                lc,
                optlevel,
                tfflags,
                tcflags,
                tlflags,
                srcfiles,
                target,
                arch,
                sharedobject,
            )

            # build the command list for the Windows batch file
            cmdlists = [
                batchfile,
            ]
        except:
            errmsg = "Could not make x64 target: {}\n".format(target)
            errmsg += traceback.print_exc()
            print(errmsg)

    else:
        if sharedobject:
            program_path, ext = os.path.splitext(target)
            if _get_osname() == "win32":
                if ext.lower() != ".dll":
                    target = program_path + ".dll"
            elif _get_osname() == "darwin":
                if ext.lower() != ".dylib":
                    target = program_path + ".dylib"
            else:
                if ext.lower() != ".so":
                    target = program_path + ".so"

        # initialize the commands and object files list
        cmdlists = []
        objfiles = []

        # assume that header files may be in other folders, so make a list
        searchdir = []
        for f in srcfiles:
            dirname = os.path.dirname(f)
            if dirname not in searchdir:
                searchdir.append(dirname)

        # build the command for each source file and add to the
        # list of commands
        for srcfile in srcfiles:
            cmdlist = []
            iscfile = False
            ext = os.path.splitext(srcfile)[1].lower()
            if ext in [".c", ".cpp"]:  # mja
                iscfile = True
                cmdlist.append(cc)  # mja
                cmdlist.append(optlevel)
                for switch in tcflags:  # mja
                    cmdlist.append(switch)  # mja
            else:  # mja
                # build command list
                cmdlist.append(fc)
                cmdlist.append(optlevel)
                for switch in tfflags:
                    cmdlist.append(switch)
                # add preprocessor option, if necessary
                if _preprocess_file(srcfile):
                    if fc == "gfortran":
                        pp_tag = "-cpp"
                    else:
                        pp_tag = "-fpp"
                    cmdlist.append(pp_tag)

            # add search path for any c and c++ header files
            if iscfile:
                for sd in searchdir:
                    cmdlist.append("-I{}".format(sd))
            # put object files and module files in objdir_temp and moddir_temp
            else:
                cmdlist.append("-I{}".format(objdir_temp))
                if fc in ["ifort", "mpiifort"]:
                    cmdlist.append("-module")
                    cmdlist.append(moddir_temp + "/")
                else:
                    cmdlist.append("-J{}".format(moddir_temp))

            cmdlist.append("-c")
            cmdlist.append(srcfile)

            # object file name and location
            srcname, srcext = os.path.splitext(srcfile)
            srcname = srcname.split(os.path.sep)[-1]
            objfile = os.path.join(objdir_temp, srcname + ".o")
            cmdlist.append("-o")
            cmdlist.append(objfile)

            # Save the name of the object file for linker
            objfiles.append(objfile)

            # If expedited, then check if object file is out of date, if it
            # exists. No need to compile if object file is newer.
            compilefile = True
            if expedite:
                if not _check_out_of_date(srcfile, objfile):
                    compilefile = False

            if compilefile:
                cmdlists.append(cmdlist)

        # Build the link command and then link to create the executable
        ilink = len(cmdlists)
        if ilink > 0:
            cmdlist = [lc, optlevel]
            cmdlist.append("-o")
            cmdlist.append(target)
            for objfile in objfiles:
                cmdlist.append(objfile)

            # linker switches
            for switch in tlflags:
                cmdlist.append(switch)

            # add linker command to the commands list
            cmdlists.append(cmdlist)

    # execute each command in cmdlists
    if not dryrun:
        for idx, cmdlist in enumerate(cmdlists):
            if idx == 0:
                if intelwin:
                    msg = (
                        "\nCompiling '{}' ".format(os.path.basename(target))
                        + "for Windows using Intel compilers..."
                    )
                else:
                    msg = "\nCompiling object files for " + "'{}'...".format(
                        os.path.basename(target)
                    )
                print(msg)
            if idx > 0 and idx == ilink:
                msg = "\nLinking object files " + "to make '{}'...".format(
                    os.path.basename(target)
                )
                print(msg)

            # write the command to the terminal
            _process_Popen_command(False, cmdlist)

            # run the command using Popen
            proc = _process_Popen_initialize(cmdlist, intelwin)

            # write batch file execution to terminal
            if intelwin:
                _process_Popen_stdout(proc)
            # establish communicator to report errors
            else:
                _process_Popen_communicate(proc)

            # evaluate return code
            returncode = proc.returncode
            if returncode != 0:
                msg = "compilation failed on '{}'".format(" ".join(cmdlist))
                print(msg)
                break

    # print blank line separator after all commands in cmdlist are executed
    print("")

    # return
    return returncode


def _create_win_batch(
    batchfile,
    fc,
    cc,
    lc,
    optlevel,
    fflags,
    cflags,
    lflags,
    srcfiles,
    target,
    arch,
    sharedobject,
):
    """Make an intel compiler batch file for compiling on windows.

    Parameters
    -------
    batchfile : str
        batch file name to create
    fc : str
        fortran compiler
    cc : str
        c or cpp compiler
    lc : str
        compiler to use for linking
    optlevel : str
        compiler optimization switch
    fflags : list
        user provided list of fortran compiler flags
    cflags : list
        user provided list of c or cpp compiler flags
    lflags : list
        linker compiler flags, which are a combination of user provided list
        of compiler flags for the compiler to used for linking
    srcfiles : list
        list of source file names
    target : str
        path for executable to create
    arch : str
        architecture to use for Intel Compilers on Windows (default is intel64)

    Returns
    -------

    """
    # determine intel version
    intel_setvars = None
    # oneAPI
    oneapi_list = ("LATEST_VERSION", "ONEAPI_ROOT")
    for on_env_var in oneapi_list:
        latest_version = os.environ.get(on_env_var)
        if latest_version is not None:
            if on_env_var == oneapi_list[0]:
                cpvars = (
                    "C:\\Program Files (x86)\\Intel\\oneAPI\\compiler\\"
                    + "{}\\env\\vars.bat".format(latest_version)
                )
            else:
                cpvars = (
                    "C:\\Program Files (x86)\\Intel\\oneAPI\\" + "setvars.bat"
                )
            if not os.path.isfile(cpvars):
                raise Exception("Could not find cpvars: {}".format(cpvars))
            intel_setvars = '"{}"'.format(cpvars)
            break
    # stand alone intel installation
    if intel_setvars is None:
        iflist = ["IFORT_COMPILER{}".format(i) for i in range(30, 12, -1)]
        for ift in iflist:
            stand_alone_intel = os.environ.get(ift)
            if stand_alone_intel is not None:
                cpvars = os.path.join(
                    stand_alone_intel, "bin", "compilervars.bat"
                )
                if not os.path.isfile(cpvars):
                    raise Exception("Could not find cpvars: {}".format(cpvars))
                intel_setvars = '"' + os.path.normpath(cpvars) + '" ' + arch
                break
    # check if either OneAPI or stand alone intel is installed
    if intel_setvars is None:
        err_msg = (
            "OneAPI or stand alone version of Intel compilers "
            + "is not installed"
        )
        raise ValueError(err_msg)

    # open the batch file
    f = open(batchfile, "w")

    # write the compilervars batch command to batchfile
    line = "call " + intel_setvars + "\n"
    f.write(line)

    # assume that header files may be in other folders, so make a list
    searchdir = []
    for s in srcfiles:
        dirname = os.path.dirname(s)
        if dirname not in searchdir:
            searchdir.append(dirname)

    # write commands to build object files
    line = (
        "echo Creating object files to create '"
        + os.path.basename(target)
        + "'\n"
    )
    f.write(line)
    for srcfile in srcfiles:
        if srcfile.endswith(".c") or srcfile.endswith(".cpp"):
            cmd = cc + " " + optlevel + " "
            for switch in cflags:
                cmd += switch + " "
            cmd += "/c" + " "

            # add search path for any header files
            for sd in searchdir:
                cmd += "/I{} ".format(sd)

            obj = os.path.join(
                objdir_temp,
                os.path.splitext(os.path.basename(srcfile))[0] + ".obj",
            )
            cmd += "/Fo:" + obj + " "
            cmd += srcfile
        else:
            cmd = fc + " " + optlevel + " "
            for switch in fflags:
                cmd += switch + " "
            # add preprocessor option, if necessary
            if _preprocess_file(srcfile):
                cmd += "/fpp" + " "
            cmd += "/c" + " "
            cmd += "/module:{0}\\ ".format(moddir_temp)
            cmd += "/object:{0}\\ ".format(objdir_temp)
            cmd += srcfile
        f.write("echo {}\n".format(cmd))
        f.write(cmd + "\n")

    # write commands to link
    line = (
        "echo Linking object files to create '"
        + os.path.basename(target)
        + "'\n"
    )
    f.write(line)

    # assemble the link command
    cmd = lc + " " + optlevel
    cmd += " " + "-o" + " " + target + " " + objdir_temp + "\\*.obj"
    for switch in lflags:
        cmd += " " + switch
    cmd += "\n"
    f.write("echo {}\n".format(cmd))
    f.write(cmd)

    # close the batch file
    f.close()

    return


def _create_makefile(
    target,
    srcdir,
    srcdir2,
    extrafiles,
    srcfiles,
    debug,
    double,
    fc,
    cc,
    fflags,
    cflags,
    syslibs,
    verbose,
    makedefaults="makedefaults",
):
    """

    Parameters
    ----------
    target : str
        path for executable to create
    srcdir : str
        path for directory containing source files
    srcdir2 : str
        additional directory with common source files.
    extrafiles : str
        path for extrafiles file that contains paths to additional source
        files to include
    srcfiles : list
        ordered list of source files to include in the makefile
    debug : bool
        boolean indicating is a debug executable will be built
    double : bool
        boolean indicating a compiler switch will be used to create an
        executable with double precision real variables.
    fc : str
        fortran compiler
    cc : str
        c or cpp compiler
    fflags : list
        user provided list of fortran compiler flags
    cflags : list
        user provided list of c or cpp compiler flags
    syslibs : list
        user provided syslibs
    makedefaults : str
        name of the makedefaults file to create with makefile (default is
        makedefaults)

    Returns
    -------

    """
    # write a message
    if verbose:
        msg = "\nWriting makefile and {}".format(makedefaults)
        print(msg)

    # set object extension
    objext = ".o"

    # get list of unique fortran and c/c++ file extensions
    fext = _get_fortran_files(srcfiles, extensions=True)
    cext = _get_c_files(srcfiles, extensions=True)

    # determine if the fortran file should be preprocessed
    if fext is None:
        preprocess = False
    else:
        preprocess = _preprocess_file(_get_fortran_files(srcfiles))

    # set exe_name
    exe_name = os.path.splitext(os.path.basename(target))[0]

    # build heading
    heading = (
        f"# makefile created by pymake (version {__version__}) "
        f"for the '{exe_name}' executable.\n"
    )

    # open makefile
    f = open("makefile", "w")

    # write header
    f.write(heading + "\n")

    #  write include file
    line = f"\ninclude ./{makedefaults}\n\n"
    f.write(line)

    # determine the directories with source files
    # source files in sdir and sdir2
    dirs = [d[0].replace("\\", "/") for d in os.walk(srcdir)]
    if srcdir2 is not None:
        dirs2 = [d[0].replace("\\", "/") for d in os.walk(srcdir2)]
        dirs = dirs + dirs2

    # source files in extrafiles
    files = _get_extra_exclude_files(extrafiles)
    if files is not None:
        for ef in files:
            fdir = os.path.dirname(ef)
            rdir = os.path.relpath(fdir, os.getcwd())
            rdir = rdir.replace("\\", "/")
            if rdir not in dirs:
                dirs.append(rdir)

    # write directories with source files and create vpath data
    line = "# Define the source file directories\n"
    f.write(line)
    vpaths = []
    for idx, source_dir in enumerate(dirs):
        vpaths.append(f"SOURCEDIR{idx + 1}")
        line = f"{vpaths[idx]}={source_dir}\n"
        f.write(line)
    f.write("\n")

    # write vpath
    f.write("VPATH = \\\n")
    for idx, sd in enumerate(vpaths):
        f.write("${" + f"{sd}" + "} ")
        if idx + 1 < len(vpaths):
            f.write("\\")
        f.write("\n")
    f.write("\n")

    # write file extensions
    line = ".SUFFIXES: "
    if fext is not None:
        for ext in fext:
            line += f"{ext} "
    if cext is not None:
        for ext in cext:
            line += f"{ext} "
    line += objext
    f.write(f"{line}\n")
    f.write("\n")

    f.write("OBJECTS = \\\n")
    for idx, srcfile in enumerate(srcfiles):
        objpth = os.path.splitext(os.path.basename(srcfile))[0] + objext
        f.write(f"$(OBJDIR)/{objpth}")
        if idx + 1 < len(srcfiles):
            f.write(" \\")
        f.write("\n")
    f.write("\n")

    f.write("# Define the objects that make up the program\n")
    f.write("$(PROGRAM) : $(OBJECTS)\n")
    if fext is None:
        line = "\t-$(CC) $(OPTLEVEL) -o $@ $(OBJECTS) $(LDFLAGS)\n"
    else:
        line = "\t-$(FC) $(OPTLEVEL) -o $@ $(OBJECTS) $(LDFLAGS)\n"
    f.write("{}\n".format(line))

    if fext is not None:
        for ext in fext:
            f.write(f"$(OBJDIR)/%{objext} : %{ext}\n")
            f.write("\t@mkdir -p $(@D)\n")
            line = (
                "\t$(FC) $(OPTLEVEL) $(FFLAGS) -c $< -o $@ "
                + "$(INCSWITCH) $(MODSWITCH)\n"
            )
            f.write(f"{line}\n")

    if cext is not None:
        for ext in cext:
            f.write(f"$(OBJDIR)/%{objext} : %{ext}\n")
            f.write("\t@mkdir -p $(@D)\n")
            line = (
                "\t$(CC) $(OPTLEVEL) $(CFLAGS) -c $< -o $@ " + "$(INCSWITCH)\n"
            )
            f.write("{}\n".format(line))

    # close the makefile
    f.close()

    # open makedefaults
    f = open(makedefaults, "w")

    # replace makefile in heading with makedefaults
    heading = heading.replace("makefile", makedefaults)

    # write header
    f.write(heading + "\n")

    # write OS evaluation
    line = "# determine OS\n"
    line += "ifeq ($(OS), Windows_NT)\n"
    line += "\tdetected_OS = Windows\n"
    line += "\tOS_macro = -D_WIN32\n"
    line += "else\n"
    line += (
        "\tdetected_OS = $(shell sh -c 'uname 2>/dev/null "
        + "|| echo Unknown')\n"
    )
    line += "\tifeq ($(detected_OS), Darwin)\n"
    line += "\t\tOS_macro = -D__APPLE__\n"
    line += "\telse\n"
    line += "\t\tOS_macro = -D__LINUX__\n"
    line += "\tendif\n"
    line += "endif\n\n"
    f.write(line)

    # get path to executable
    dpth = os.path.dirname(target)
    if len(dpth) > 0:
        dpth = os.path.relpath(dpth)
    else:
        dpth = "."

    # write
    line = (
        "# Define the directories for the object and module files\n"
        + "# and the executable and its path.\n"
    )
    line += f"BINDIR = {dpth}\n"
    line += f"OBJDIR = {objdir_temp}\n"
    line += f"MODDIR = {moddir_temp}\n"
    line += "INCSWITCH = -I $(OBJDIR)\n"
    line += "MODSWITCH = -J $(MODDIR)\n\n"
    f.write(line)

    line = "# define program name\n"
    line += f"PROGRAM = $(BINDIR)/{exe_name}\n\n"
    f.write(line)

    line = "# define os dependent program name\n"
    line += "ifeq ($(detected_OS), Windows)\n"
    line += f"\tPROGRAM = $(BINDIR)/{exe_name}.exe\n"
    line += "endif\n\n"
    f.write(line)

    # reassign compilers if the defined compilers do not exist
    line = "# use GNU compilers if defined compilers do not exist\n"
    line += "ifeq ($(detected_OS), Windows)\n"
    line += "\tWHICH = where\n"
    line += "else\n"
    line += "\tWHICH = which\n"
    line += "endif\n"
    if fext is not None:
        line += "ifeq (, $(shell $(WHICH) $(FC)))\n"
        line += "\tFC = gfortran\n"
        line += "endif\n"
    if cext is not None:
        line += "ifeq (, $(shell $(WHICH) $(CC)))\n"
        line += "\tCC = gcc\n"
        line += "endif\n"
    line += "\n"
    f.write(line)

    # set gfortran as fortran compiler if it is f77
    if fext is not None:
        line = "# set fortran compiler to gfortran if it is f77\n"
        line += "ifeq ($(FC), f77)\n"
        line += "\tFC = gfortran\n"
        line += "\t# set c compiler to gcc if not passed on the command line\n"
        line += '\tifneq ($(origin CC), "command line")\n'
        line += "\t\tifneq ($(CC), gcc)\n"
        line += "\t\t\tCC = gcc\n"
        line += "\t\tendif\n"
        line += "\tendif\n"
        line += "endif\n\n"
        f.write(line)
    else:
        line = "# set cc compiler to gcc if it is cc\n"
        line += "ifeq ($(CC), cc)\n"
        line += "\tCC = gcc\n"
        line += "endif\n\n"
        f.write(line)

    # optimization level
    optlevel = _get_optlevel(
        target, fc, cc, debug, fflags, cflags, verbose=verbose
    )
    line = "# set the optimization level (OPTLEVEL) if not defined\n"
    line += "OPTLEVEL ?= {}\n\n".format(optlevel.replace("/", "-"))
    f.write(line)

    # fortran flags
    if fext is not None:
        # remove existing os_macro for machine OS from fflags prior to
        # adding os_macro for specific OS
        tag = "-" + _get_os_macro()
        if tag in fflags:
            fflags.remove(tag)

        # build fortran flags for each os
        line = "# set the fortran flags\n"
        line += "ifeq ($(detected_OS), Windows)\n"
        line += "\tifeq ($(FC), gfortran)\n"
        tfflags = _get_fortran_flags(
            target,
            "gfortran",
            [],
            debug,
            double,
            osname="win32",
            verbose=verbose,
        )
        for idx, flag in enumerate(tfflags):
            if "-D_" in flag:
                tfflags[idx] = "$(OS_macro)"
        if preprocess:
            tfflags.append("-cpp")
        line += "\t\tFFLAGS ?= {}\n".format(" ".join(tfflags))
        line += "\tendif\n"
        line += "else\n"
        line += "\tifeq ($(FC), gfortran)\n"
        tfflags = _get_fortran_flags(
            target,
            "gfortran",
            [],
            debug,
            double,
            osname="linux",
            verbose=verbose,
        )
        for idx, flag in enumerate(tfflags):
            if "-D__" in flag:
                tfflags[idx] = "$(OS_macro)"
        if preprocess:
            tfflags.append("-cpp")
        line += "\t\tFFLAGS ?= {}\n".format(" ".join(tfflags))
        line += "\tendif\n"
        line += "\tifeq ($(FC), $(filter $(FC), ifort mpiifort))\n"
        tfflags = _get_fortran_flags(
            target,
            "ifort",
            [],
            debug,
            double,
            osname="linux",
            verbose=verbose,
        )
        for idx, flag in enumerate(tfflags):
            if "-D__" in flag:
                tfflags[idx] = "$(OS_macro)"
        if preprocess:
            tfflags.append("-fpp")
        line += "\t\tFFLAGS ?= {}\n".format(" ".join(tfflags))
        line += "\t\tMODSWITCH = -module $(MODDIR)\n"
        line += "\tendif\n"
        line += "endif\n\n"
        f.write(line)

    # c/c++ flags
    if cext is not None:
        line = "# set the c/c++ flags\n"
        line += "ifeq ($(detected_OS), Windows)\n"
        line += "\tifeq ($(CC), $(filter $(CC), gcc g++))\n"
        tcflags = _get_c_flags(
            target,
            "gcc",
            fflags,
            debug,
            srcfiles,
            osname="win32",
            verbose=verbose,
        )
        line += "\t\tCFLAGS ?= {}\n".format(" ".join(tcflags))
        line += "\tendif\n"
        line += "\tifeq ($(CC), $(filter $(CC), clang clang++))\n"
        tcflags = _get_c_flags(
            target,
            "clang",
            fflags,
            debug,
            srcfiles,
            osname="win32",
            verbose=verbose,
        )
        line += "\t\tCFLAGS ?= {}\n".format(" ".join(tcflags))
        line += "\tendif\n"
        line += "else\n"
        line += "\tifeq ($(CC), $(filter $(CC), gcc g++))\n"
        tcflags = _get_c_flags(
            target,
            "gcc",
            fflags,
            debug,
            srcfiles,
            osname="linux",
            verbose=verbose,
        )
        line += "\t\tCFLAGS ?= {}\n".format(" ".join(tcflags))
        line += "\tendif\n"
        line += "\tifeq ($(CC), $(filter $(CC), clang clang++))\n"
        tcflags = _get_c_flags(
            target,
            "clang",
            fflags,
            debug,
            srcfiles,
            osname="linux",
            verbose=verbose,
        )
        line += "\t\tCFLAGS ?= {}\n".format(" ".join(tcflags))
        line += "\tendif\n"
        line += "\tifeq ($(CC), $(filter $(CC), icc mpiicc icpc))\n"
        tcflags = _get_c_flags(
            target,
            "icc",
            fflags,
            debug,
            srcfiles,
            osname="linux",
            verbose=verbose,
        )
        line += "\t\tCFLAGS ?= {}\n".format(" ".join(tcflags))
        line += "\tendif\n"
        line += "endif\n\n"
        f.write(line)

    # syslibs
    line = "# set the ldflgs\n"
    # windows - gfortran only
    line += "ifeq ($(detected_OS), Windows)\n"
    # c/c++ compiler used for linking
    if fext is None:
        _, tsyslibs = _get_linker_flags(
            target,
            None,
            "gcc",
            [],
            srcfiles,
            osname="win32",
            verbose=verbose,
        )
        line += "\tifeq ($(CC), $(filter $(CC), gcc g++))\n"
        line += "\t\tLDFLAGS ?= {}\n".format(" ".join(tsyslibs))
        line += "\tendif\n"
        _, tsyslibs = _get_linker_flags(
            target,
            None,
            "clang",
            [],
            srcfiles,
            osname="win32",
            verbose=verbose,
        )
        line += "\tifeq ($(CC), $(filter $(CC), clang clang++))\n"
        line += "\t\tLDFLAGS ?= {}\n".format(" ".join(tsyslibs))
        line += "\tendif\n"
    # fortran compiler used for linking
    else:
        _, tsyslibs = _get_linker_flags(
            target,
            "gfortran",
            "gcc",
            [],
            srcfiles,
            osname="win32",
            verbose=verbose,
        )
        line += "\tifeq ($(FC), $(filter $(FC), gfortran))\n"
        line += "\t\tLDFLAGS ?= {}\n".format(" ".join(tsyslibs))
        line += "\tendif\n"
    # linux and osx
    line += "else\n"
    # c/c++ compiler used for linking
    if fext is None:
        _, tsyslibs = _get_linker_flags(
            target,
            None,
            "gcc",
            [],
            srcfiles,
            osname="linux",
            verbose=verbose,
        )
        line += "\tifeq ($(CC), $(filter $(CC), gcc g++))\n"
        line += "\t\tLDFLAGS ?= {}\n".format(" ".join(tsyslibs))
        line += "\tendif\n"
        _, tsyslibs = _get_linker_flags(
            target,
            None,
            "clang",
            [],
            srcfiles,
            osname="linux",
            verbose=verbose,
        )
        line += "\tifeq ($(CC), $(filter $(CC), clang clang++))\n"
        line += "\t\tLDFLAGS ?= {}\n".format(" ".join(tsyslibs))
        line += "\tendif\n"
    # fortran compiler used for linking
    else:
        # gfortran compiler
        line += "\tifeq ($(FC), gfortran)\n"
        _, tsyslibs = _get_linker_flags(
            target,
            "gfortran",
            "gcc",
            [],
            srcfiles,
            osname="linux",
            verbose=verbose,
        )
        line += "\t\tLDFLAGS ?= {}\n".format(" ".join(tsyslibs))
        line += "\tendif\n"
        # ifort compiler
        line += "\tifeq ($(FC), $(filter $(FC), ifort mpiifort))\n"
        _, tsyslibs = _get_linker_flags(
            target,
            "ifort",
            "icc",
            [],
            srcfiles,
            osname="linux",
            verbose=verbose,
        )
        line += "\t\tLDFLAGS ?= {}\n".format(" ".join(tsyslibs))
        line += "\tendif\n"
    line += "endif\n\n"
    f.write(line)

    # check for windows error condition
    line = "# check for Windows error condition\n"
    line += "ifeq ($(detected_OS), Windows)\n"
    if fext is not None:
        line += "\tifeq ($(FC), $(filter $(FC), ifort mpiifort))\n"
        line += "\t\tWINDOWSERROR = $(FC)\n"
        line += "\tendif\n"
    if cext is not None:
        line += "\tifeq ($(CC), $(filter $(CC), icl))\n"
        line += "\t\tWINDOWSERROR = $(CC)\n"
        line += "\tendif\n"
    line += "endif\n\n"
    f.write(line)

    # task functions
    line = "# Define task functions\n"
    line += "# Create the bin directory and compile and link the program\n"
    line += "all: windowscheck makedirs | $(PROGRAM)\n\n"
    line += "# test for windows error\n"
    line += "windowscheck:\n"
    line += "ifdef WINDOWSERROR\n"
    line += "\t$(error cannot use makefile on windows with $(WINDOWSERROR))\n"
    line += "endif\n\n"
    line += "# Make the bin directory for the executable\n"
    line += "makedirs:\n"
    line += "\tmkdir -p $(BINDIR)\n"
    line += "\tmkdir -p $(MODDIR)\n\n"
    line += "# Write selected compiler settings\n"
    line += ".PHONY: settings\n"
    line += "settings:\n"
    line += '\t@echo "Optimization level: $(OPTLEVEL)"\n'
    if fext is not None:
        line += '\t@echo "Fortran compiler:   $(FC)"\n'
        line += '\t@echo "Fortran flags:      $(FFLAGS)"\n'
    if cext is not None:
        line += '\t@echo "C compiler:         $(CC)"\n'
        line += '\t@echo "C flags:            $(CFLAGS)"\n'
    if fext is None:
        line += '\t@echo "Linker:             $(CC)"\n'
    else:
        line += '\t@echo "Linker:             $(FC)"\n'
    line += '\t@echo "SYSLIBS:            $(LDFLAGS)"\n\n'
    line += "# Clean the object and module files and the executable\n"
    line += ".PHONY: clean\n"
    line += "clean:\n"
    line += "\t-rm -rf $(OBJDIR)\n"
    line += "\t-rm -rf $(MODDIR)\n"
    line += "\t-rm -rf $(PROGRAM)\n\n"
    line += "# Clean the object and module files\n"
    line += ".PHONY: cleanobj\n"
    line += "cleanobj:\n"
    line += "\t-rm -rf $(OBJDIR)\n"
    line += "\t-rm -rf $(MODDIR)\n\n"
    f.write(line)

    # close the makedefaults
    f.close()

    return
