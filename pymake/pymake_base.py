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
        double=args.double,
        debug=args.debug,
        include_subdirs=args.subdirs,
        fflags=args.fflags,
        cflags=args.cflags,
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
import shutil
import sys
import warnings
from pathlib import Path
from textwrap import dedent

from .utils._compiler_language_files import (
    _get_c_files,
    _get_fortran_files,
    _get_ordered_srcfiles,
    _get_srcfiles,
    _preprocess_file,
)
from .utils._compiler_switches import (
    _get_c_flags,
    _get_fortran_flags,
    _get_linker_flags,
    _get_optlevel,
    _get_os_macro,
)
from .utils._file_utils import _get_extra_exclude_files
from .utils._meson_build import _meson_build


def main(
    srcdir=None,
    target=None,
    fc="gfortran",
    cc="gcc",
    makeclean=True,
    double=False,
    debug=False,
    include_subdirs=False,
    fflags=None,
    cflags=None,
    syslibs=None,
    makefile=False,
    makefile_only=False,
    dryrun=None,
    makefiledir=".",
    srcdir2=None,
    extrafiles=None,
    excludefiles=None,
    sharedobject=False,
    appdir=None,
    verbose=False,
    inplace=False,
    networkx=False,
    mesondir=None,
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
    makefile : bool
        boolean indicating if a GNU make makefile should be created
    makefile_only : bool
        boolean indicating if a GNU make makefile should be created without
        building the target (default is False)
    dryrun : bool
        deprecated name for makefile_only, which replaced it when the pymake
        build engine was removed (default is None)
    makefiledir : str
        GNU make makefile path
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
        defined in extrafiles will be used directly. If inplace is False,
        source files will be copied to a directory named srcdir_temp.
        (default is False)
    networkx : bool
        boolean indicating that the NetworkX python package will be used to
        create the Directed Acyclic Graph (DAG) used to determine the order
        source files are compiled in. The NetworkX package tends to result in
        a unique DAG more often than the standard algorithm used in pymake.
        (default is False)
    mesondir : str
        Main meson.build file path. the current directory is used when
        mesondir is None (default is None)

    Returns
    -------
    returncode : int
        return code

    """
    # dryrun wrote a makefile without building the target, which is what
    # makefile_only does, so it is still accepted
    if dryrun is not None:
        warnings.warn(
            "dryrun is deprecated and will be removed in a future release, "
            "use makefile_only instead",
            DeprecationWarning,
            stacklevel=2,
        )
        makefile_only = makefile_only or dryrun

    # a makefile is written from the source files pymake finds, so the
    # source is still processed when only a makefile is asked for
    if makefile_only:
        makefile = True

    # meson builds the source where it is
    if not inplace and not makefile_only:
        inplace = True
        print(
            f"Using meson to build {os.path.basename(target)}, "
            "resetting inplace to True"
        )

    if srcdir is not None and target is not None:
        objdir_temp, moddir_temp, srcdir_temp = get_temporary_directories(
            appdir=appdir, target=Path(target).stem
        )
        if inplace:
            srcdir_temp = srcdir

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
                "Nothing to do the fortran (-fc) and c/c++ compilers (-cc) "
                "are both 'none'."
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
            print(f"\nsource files are in:\n    {srcdir}\n")
            print(f"executable name to be created:\n    {target}\n")
            if srcdir2 is not None:
                msg = "additional source files are in:\n" + f"     {srcdir2}\n"
                print(msg)

        # a meson build file belongs with the source, and the current
        # directory is used when a directory was not asked for
        if mesondir is None:
            mesondir = "."

        # make sure the path for the target exists
        pth = os.path.dirname(target)
        if pth == "":
            pth = "."
        if not os.path.exists(pth):
            print(f"creating target path - {pth}\n")
            os.makedirs(pth)

        # initialize
        srcfiles = _pymake_initialize(
            srcdir,
            target,
            srcdir2,
            extrafiles,
            excludefiles,
            include_subdirs,
            objdir_temp,
            moddir_temp,
            srcdir_temp,
        )

        # get ordered list of files to compile
        srcfiles = _get_ordered_srcfiles(srcfiles, networkx)

        # update openspec files
        _create_openspec(srcfiles, verbose)

        # a meson build file that is already there was provided by the
        # target rather than written by pymake, so it is not a temporary file
        meson_provided = os.path.isfile(os.path.join(mesondir, "meson.build"))

        # compile the executable, unless only a makefile was asked for
        if makefile_only:
            returncode = 0
        else:
            returncode = _meson_build(
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
                sharedobject,
                mesondir,
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
                sharedobject,
                makefiledir,
                verbose,
            )

        # clean up temporary files
        if makeclean and returncode == 0:
            _clean_temp_files(
                target,
                inplace,
                objdir_temp,
                moddir_temp,
                srcdir_temp,
                mesondir,
                verbose,
                meson_provided=meson_provided,
            )
    else:
        msg = (
            f"Nothing to do, the srcdir ({srcdir}) and/or target ({target}) "
            "are not specified."
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
    objdir_temp,
    moddir_temp,
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
    objdir_temp : str
        path for temporary directory that will contain the object files.
    moddir_temp : str
        path for temporary directory that will contain the module files.
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
                srcdir, srcdir_temp, ignore=shutil.ignore_patterns(*excludefiles)
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
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*excludefiles))
            else:
                shutil.copytree(src, dst)
        else:
            dst = os.path.relpath(os.path.abspath(os.path.abspath(commonsrc)))

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
                    msg = f"Current working directory: {os.getcwd()}\n"
                    msg += f"Error in extrafiles: {extrafiles}\n"
                    msg += f"Could not find file: {fpth}"
                    raise FileNotFoundError(msg)
        if inplace:
            dst = os.path.normpath(os.path.relpath(fpth, os.getcwd()))
        else:
            dst = os.path.join(srcdir_temp, os.path.basename(fpth))
            if os.path.isfile(dst):
                raise ValueError(
                    "Error with extrafile.  Name conflicts with "
                    f"an existing source file: {dst}"
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

    return srcfiles


def get_temporary_directories(appdir=None, target=None):
    """Get paths to temporary object, module, and source files.

    Parameters
    ----------
    appdir : str
        path for executable
    target : str
        target name to be appended to the temporary directories.
        Default is None

    Returns
    -------
    obj_temp : str
        path to temporary object files
    mod_temp : str
        path to temporary module files
    src_temp : str
        path to temporary source files

    """
    if appdir is None:
        base_pth = "."
    else:
        base_pth = appdir
    if target is None:
        target = "temp"
    return (
        os.path.join(base_pth, f"obj_{target}"),
        os.path.join(base_pth, f"mod_{target}"),
        os.path.join(base_pth, f"src_{target}"),
    )


def _clean_temp_files(
    target,
    inplace,
    objdir_temp,
    moddir_temp,
    srcdir_temp,
    mesondir,
    verbose=False,
    meson_provided=False,
):
    """Cleanup intermediate files. Remove mod and object files, and remove the
    temporary source directory.

    Parameters
    ----------
    target : str
        path for executable to create
    inplace : bool
        boolean indicating that the source files in srcdir, srcdir2, and
        defined in extrafiles will be used directly. If inplace is True,
        source files will be copied to a directory named srcdir_temp.
        (default is False)
    objdir_temp : str
        path for temporary directory that will contain the object files.
    moddir_temp : str
        path for temporary directory that will contain the module files.
    srcdir_temp : str
        path for directory that will contain the source files. If
        srcdir_temp is the same as srcdir then the original source files
        will be used.
    mesondir : str
        Main meson.build file path. the current directory is used when
        mesondir is None (default is None)
    verbose : bool
        boolean indicating if output will be printed to the terminal
    meson_provided : bool
        boolean indicating that the meson build file was provided by the
        target, in which case it is not removed (default is False)

    Returns
    -------
    None

    """
    # clean things up
    if verbose:
        print("\nCleaning up temporary source, object, and module files...")
    filelist = os.listdir(".")
    delext = [".mod", ".o", ".obj"]
    for f in filelist:
        for ext in delext:
            if f.endswith(ext):
                if verbose:
                    print(f"    removing...{f}")
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
                    print(f"    removing...'{fpth}'")
                os.remove(fpth)

    # remove temporary directories
    if verbose:
        msg = "\nCleaning up temporary source, object, and module directories..."
        print(msg)
    if not inplace:
        if os.path.isdir(srcdir_temp):
            if verbose:
                print(f"removing...'{srcdir_temp}'")
            shutil.rmtree(srcdir_temp)
    if os.path.isdir(objdir_temp):
        if verbose:
            print(f"removing...'{objdir_temp}'")
        shutil.rmtree(objdir_temp)
    if os.path.isdir(moddir_temp):
        if verbose:
            print(f"removing...'{moddir_temp}'")
        shutil.rmtree(moddir_temp)
    meson_builddir = os.path.join(mesondir, "_build")
    if os.path.isdir(meson_builddir):
        if verbose:
            print(f"removing...'{meson_builddir}'")
        shutil.rmtree(meson_builddir)
    # a build file the target provides is not a file pymake wrote
    if not meson_provided:
        main_meson_file = os.path.join(mesondir, "meson.build")
        if os.path.isfile(main_meson_file):
            if verbose:
                print(f"removing...'{main_meson_file}'")
            os.remove(main_meson_file)
    return


def _openspec_content():
    """Return the contents of the openspec include file pymake writes.

    Returns
    -------
    content : str
        the include file contents

    """
    return dedent("""\
        c -- created by pymake_base.py
              CHARACTER*20 ACCESS,FORM,ACTION(2)
              DATA ACCESS/'STREAM'/
              DATA FORM/'UNFORMATTED'/
              DATA (ACTION(I),I=1,2)/'READ','READWRITE'/
        c -- end of include file
    """)


def _create_openspec(srcfiles, verbose):
    """Create new openspec.inc, FILESPEC.INC, and filespec.inc files that uses
    STREAM ACCESS. This is specific to MODFLOW and MT3D based targets. Source
    directories are scanned and files defining file access are replaced.

    Parameters
    ----------
    srcfiles : list
        list of source files to be compiled
    verbose: bool
        boolean indicating if output will be printed to the terminal

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
                    print(f'replacing..."{fpth}"')
                with open(fpth, "w") as f:
                    f.write(_openspec_content())


def _makefile_compiler_ifeq(variable, compilers, indent="\t"):
    """Build a makefile conditional that matches a compiler.

    A version suffix, for example 'gfortran-13', is also matched.

    Parameters
    ----------
    variable : str
        makefile compiler variable name ('FC' or 'CC')
    compilers : list
        base compiler names to match
    indent : str
        string prepended to the conditional

    Returns
    -------
    line : str
        makefile conditional

    """
    patterns = []
    for compiler in compilers:
        patterns += [compiler, f"{compiler}-%"]

    return (
        f"{indent}ifeq ($({variable}), $(filter {' '.join(patterns)}, $({variable})))\n"
    )


def _makefile_path(pth):
    """Format a path so that it can be written to a makefile.

    A makefile pymake writes is used on every operating system pymake builds
    on, so a path in one is written with a forward slash separator whichever
    separator the operating system it was written on uses.

    Parameters
    ----------
    pth : str or Path
        path to format

    Returns
    -------
    pth : str
        path with a forward slash separator

    """
    return Path(pth).as_posix()


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
    sharedobject,
    makefiledir,
    verbose,
    makedefaults="makedefaults",
):
    """Write a GNU make makefile and makedefaults file for the target.

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
    sharedobject : bool
        boolean indicating a shared object will be built
    makefiledir : str
        GNU make makefile path
    verbose : bool
        boolean indicating if output will be printed to the terminal
    makedefaults : str
        name of the makedefaults file to create with makefile (default is
        makedefaults)

    Returns
    -------

    """
    # write a message
    if verbose:
        msg = f"\nWriting makefile and {makedefaults}"
        print(msg)

    # set executable extension
    if sharedobject:
        win_ext = ".dll"
        macos_ext = ".dylib"
        linux_ext = ".so"
    else:
        win_ext = ".exe"
        macos_ext = ""
        linux_ext = ""

    # set makefile directory
    make_dir = makefiledir

    # get temporary directories
    objdir_temp, moddir_temp, _ = get_temporary_directories(make_dir)

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
    heading = f"# makefile created by pymake for the '{exe_name}' executable.\n"

    # open makefile

    _write_makefile(
        make_dir,
        heading,
        makedefaults,
        srcdir,
        srcdir2,
        extrafiles,
        srcfiles,
        fext,
        cext,
        objext,
    )

    _write_makedefaults(
        make_dir,
        heading,
        makedefaults,
        target,
        exe_name,
        fc,
        cc,
        fflags,
        cflags,
        debug,
        double,
        sharedobject,
        preprocess,
        objdir_temp,
        moddir_temp,
        fext,
        cext,
        win_ext,
        linux_ext,
        macos_ext,
        srcfiles,
        verbose,
    )

    # replace windows line endings
    if sys.platform == "win32":
        windows_line_ending = b"\r\n"
        unix_line_ending = b"\n"
        for file in (
            os.path.join(make_dir, "makefile"),
            os.path.join(make_dir, makedefaults),
        ):
            with open(file, "rb") as f:
                content = f.read()

            # replace windows line endings
            content = content.replace(windows_line_ending, unix_line_ending)

            # rewrite the file
            with open(file, "wb") as f:
                f.write(content)

    return


def _write_makefile(
    make_dir,
    heading,
    makedefaults,
    srcdir,
    srcdir2,
    extrafiles,
    srcfiles,
    fext,
    cext,
    objext,
):
    """Write the makefile, which lists the source files and the rules.

    Returns
    -------
    None

    """
    # the file is written a line at a time, so the function is long and
    # takes what every line it writes needs
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    # pylint: disable=too-complex
    f = open(os.path.join(make_dir, "makefile"), "w")

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
    dirs = sorted(dirs)

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
        rel_source_dir = _makefile_path(os.path.relpath(source_dir, make_dir))
        vpaths.append(f"SOURCEDIR{idx + 1}")
        line = f"{vpaths[idx]}={rel_source_dir}\n"
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
    f.write(line)
    f.write("\n\n")

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
    f.write(f"{line}\n")

    if fext is not None:
        for ext in fext:
            f.write(f"$(OBJDIR)/%{objext} : %{ext}\n")
            f.write("\t@mkdir -p $(@D)\n")
            line = (
                "\t$(FC) $(OPTLEVEL) $(FFLAGS) -c $< -o $@ "
                "$(INCSWITCH) $(MODSWITCH)\n\n"
            )
            f.write(line)

    if cext is not None:
        for ext in cext:
            f.write(f"$(OBJDIR)/%{objext} : %{ext}\n")
            f.write("\t@mkdir -p $(@D)\n")
            line = "\t$(CC) $(OPTLEVEL) $(CFLAGS) -c $< -o $@ $(INCSWITCH)\n\n"
            f.write(line)

    # close the makefile
    f.close()


def _write_makedefaults(
    make_dir,
    heading,
    makedefaults,
    target,
    exe_name,
    fc,
    cc,
    fflags,
    cflags,
    debug,
    double,
    sharedobject,
    preprocess,
    objdir_temp,
    moddir_temp,
    fext,
    cext,
    win_ext,
    linux_ext,
    macos_ext,
    srcfiles,
    verbose,
):
    """Write the makedefaults file, which sets the compilers and the flags.

    Returns
    -------
    None

    """
    # the file is written a line at a time, so the function is long and
    # takes what every line it writes needs
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    # pylint: disable=too-complex
    # open makedefaults
    f = open(os.path.join(make_dir, makedefaults), "w")

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
    line += "\tdetected_OS = $(shell sh -c 'uname 2>/dev/null || echo Unknown')\n"
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
        dpth = os.path.relpath(dpth, make_dir)
    else:
        dpth = "."

    # write header
    line = (
        "# Define the directories for the object and module files\n"
        "# and the executable and its path.\n"
    )
    tpth = _makefile_path(dpth)
    line += f"BINDIR = {tpth}\n"
    tpth = _makefile_path(os.path.relpath(objdir_temp, make_dir))
    line += f"OBJDIR = {tpth}\n"
    tpth = _makefile_path(os.path.relpath(moddir_temp, make_dir))
    line += f"MODDIR = {tpth}\n"
    line += "INCSWITCH = -I $(OBJDIR)\n"
    line += "MODSWITCH = -J $(MODDIR)\n\n"
    f.write(line)

    line = "# define os dependent program name\n"
    line += "ifeq ($(detected_OS), Windows)\n"
    line += f"\tPROGRAM = $(BINDIR)/{exe_name}{win_ext}\n"
    line += "else ifeq ($(detected_OS), Darwin)\n"
    line += f"\tPROGRAM = $(BINDIR)/{exe_name}{macos_ext}\n"
    line += "else\n"
    line += f"\tPROGRAM = $(BINDIR)/{exe_name}{linux_ext}\n"
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

    line = _makedefaults_flags(
        target,
        fc,
        cc,
        fflags,
        cflags,
        debug,
        double,
        sharedobject,
        preprocess,
        fext,
        cext,
        srcfiles,
        verbose,
    )
    f.write(line)

    line = _makedefaults_syslibs(
        target,
        sharedobject,
        fext,
        srcfiles,
        verbose,
    )
    f.write(line)

    line = _makedefaults_tasks(fext, cext)
    f.write(line)

    f.close()


def _makedefaults_flags(
    target,
    fc,
    cc,
    fflags,
    cflags,
    debug,
    double,
    sharedobject,
    preprocess,
    fext,
    cext,
    srcfiles,
    verbose,
):
    """Return the optimization level and the compiler flags for makedefaults.

    Returns
    -------
    text : str
        the lines that set the flags

    """
    # the lines are built one at a time from what every line needs, so
    # the function takes more than the analysis expects
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    # pylint: disable=too-many-locals,too-many-statements
    text = _makedefaults_fortran_flags(
        target,
        fc,
        cc,
        fflags,
        cflags,
        debug,
        double,
        sharedobject,
        preprocess,
        fext,
        verbose,
    )
    text += _makedefaults_c_flags(
        target,
        fflags,
        debug,
        sharedobject,
        cext,
        srcfiles,
        verbose,
    )
    return text


def _makedefaults_fortran_flags(
    target,
    fc,
    cc,
    fflags,
    cflags,
    debug,
    double,
    sharedobject,
    preprocess,
    fext,
    verbose,
):
    """Return the optimization level and the fortran flags for makedefaults.

    Returns
    -------
    text : str
        the lines that set the optimization level and the fortran flags

    """
    # the lines are built one at a time from what every line needs, so
    # the function takes more than the analysis expects
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    # pylint: disable=too-many-locals,too-many-statements
    text = ""
    # optimization level
    optlevel = _get_optlevel(target, fc, cc, debug, fflags, cflags)
    line = "# set the optimization level (OPTLEVEL) if not defined\n"
    line += f"OPTLEVEL ?= {optlevel.replace('/', '-')}\n\n"
    text += line

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
        line += _makefile_compiler_ifeq("FC", ["gfortran"])
        tfflags = _get_fortran_flags(
            target,
            "gfortran",
            [],
            debug,
            double,
            osname="win32",
            sharedobject=sharedobject,
            verbose=verbose,
        )
        for idx, flag in enumerate(tfflags):
            if "-D_" in flag:
                tfflags[idx] = "$(OS_macro)"
        if preprocess:
            tfflags.append("-cpp")
        line += f"\t\tFFLAGS ?= {' '.join(tfflags)}\n"
        line += "\tendif\n"
        line += "else\n"
        line += _makefile_compiler_ifeq("FC", ["gfortran"])
        tfflags = _get_fortran_flags(
            target,
            "gfortran",
            [],
            debug,
            double,
            osname="linux",
            sharedobject=sharedobject,
            verbose=verbose,
        )
        for idx, flag in enumerate(tfflags):
            if "-D__" in flag:
                tfflags[idx] = "$(OS_macro)"
        if preprocess:
            tfflags.append("-cpp")
        line += f"\t\tFFLAGS ?= {' '.join(tfflags)}\n"
        line += "\tendif\n"
        line += _makefile_compiler_ifeq("FC", ["ifort", "mpiifort"])
        tfflags = _get_fortran_flags(
            target,
            "ifort",
            [],
            debug,
            double,
            osname="linux",
            sharedobject=sharedobject,
            verbose=verbose,
        )
        for idx, flag in enumerate(tfflags):
            if "-D__" in flag:
                tfflags[idx] = "$(OS_macro)"
        if preprocess:
            tfflags.append("-fpp")
        line += f"\t\tFFLAGS ?= {' '.join(tfflags)}\n"
        line += "\t\tMODSWITCH = -module $(MODDIR)\n"
        line += "\tendif\n"
        line += "endif\n\n"
        text += line

    return text


def _makedefaults_c_flags(
    target,
    fflags,
    debug,
    sharedobject,
    cext,
    srcfiles,
    verbose,
):
    """Return the c and c++ flags for makedefaults.

    Returns
    -------
    text : str
        the lines that set the c and c++ flags

    """
    # the lines are built one at a time from what every line needs, so
    # the function takes more than the analysis expects
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    # pylint: disable=too-many-locals,too-many-statements
    text = ""
    # c/c++ flags
    if cext is not None:
        line = "# set the c/c++ flags\n"
        line += "ifeq ($(detected_OS), Windows)\n"
        line += _makefile_compiler_ifeq("CC", ["gcc", "g++"])
        tcflags = _get_c_flags(
            target,
            "gcc",
            fflags,
            debug,
            srcfiles,
            osname="win32",
            sharedobject=sharedobject,
            verbose=verbose,
        )
        line += f"\t\tCFLAGS ?= {' '.join(tcflags)}\n"
        line += "\tendif\n"
        line += _makefile_compiler_ifeq("CC", ["clang", "clang++"])
        tcflags = _get_c_flags(
            target,
            "clang",
            fflags,
            debug,
            srcfiles,
            osname="win32",
            sharedobject=sharedobject,
            verbose=verbose,
        )
        line += f"\t\tCFLAGS ?= {' '.join(tcflags)}\n"
        line += "\tendif\n"
        line += "else\n"
        line += _makefile_compiler_ifeq("CC", ["gcc", "g++"])
        tcflags = _get_c_flags(
            target,
            "gcc",
            fflags,
            debug,
            srcfiles,
            osname="linux",
            sharedobject=sharedobject,
            verbose=verbose,
        )
        line += f"\t\tCFLAGS ?= {' '.join(tcflags)}\n"
        line += "\tendif\n"
        line += _makefile_compiler_ifeq("CC", ["clang", "clang++"])
        tcflags = _get_c_flags(
            target,
            "clang",
            fflags,
            debug,
            srcfiles,
            osname="linux",
            sharedobject=sharedobject,
            verbose=verbose,
        )
        line += f"\t\tCFLAGS ?= {' '.join(tcflags)}\n"
        line += "\tendif\n"
        line += _makefile_compiler_ifeq("CC", ["icc", "mpiicc", "icpc"])
        tcflags = _get_c_flags(
            target,
            "icc",
            fflags,
            debug,
            srcfiles,
            osname="linux",
            sharedobject=sharedobject,
            verbose=verbose,
        )
        line += f"\t\tCFLAGS ?= {' '.join(tcflags)}\n"
        line += "\tendif\n"
        line += "endif\n\n"
        text += line

    return text


def _makedefaults_syslibs(
    target,
    sharedobject,
    fext,
    srcfiles,
    verbose,
):
    """Return the linker flags and the link commands for makedefaults.

    Returns
    -------
    line : str
        the lines that set the linker flags

    """
    text = ""
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
            sharedobject=sharedobject,
            verbose=verbose,
        )
        line += _makefile_compiler_ifeq("CC", ["gcc", "g++"])
        line += f"\t\tLDFLAGS ?= {' '.join(tsyslibs)}\n"
        line += "\tendif\n"
        _, tsyslibs = _get_linker_flags(
            target,
            None,
            "clang",
            [],
            srcfiles,
            osname="win32",
            sharedobject=sharedobject,
            verbose=verbose,
        )
        line += _makefile_compiler_ifeq("CC", ["clang", "clang++"])
        line += f"\t\tLDFLAGS ?= {' '.join(tsyslibs)}\n"
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
            sharedobject=sharedobject,
            verbose=verbose,
        )
        line += _makefile_compiler_ifeq("FC", ["gfortran"])
        line += f"\t\tLDFLAGS ?= {' '.join(tsyslibs)}\n"
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
            sharedobject=sharedobject,
            verbose=verbose,
        )
        line += _makefile_compiler_ifeq("CC", ["gcc", "g++"])
        line += f"\t\tLDFLAGS ?= {' '.join(tsyslibs)}\n"
        line += "\tendif\n"
        _, tsyslibs = _get_linker_flags(
            target,
            None,
            "clang",
            [],
            srcfiles,
            osname="linux",
            sharedobject=sharedobject,
            verbose=verbose,
        )
        line += _makefile_compiler_ifeq("CC", ["clang", "clang++"])
        line += f"\t\tLDFLAGS ?= {' '.join(tsyslibs)}\n"
        line += "\tendif\n"
    # fortran compiler used for linking
    else:
        # gfortran compiler
        line += _makefile_compiler_ifeq("FC", ["gfortran"])
        _, tsyslibs = _get_linker_flags(
            target,
            "gfortran",
            "gcc",
            [],
            srcfiles,
            osname="linux",
            sharedobject=sharedobject,
            verbose=verbose,
        )
        line += f"\t\tLDFLAGS ?= {' '.join(tsyslibs)}\n"
        line += "\tendif\n"
        # ifort compiler
        line += _makefile_compiler_ifeq("FC", ["ifort", "mpiifort"])
        _, tsyslibs = _get_linker_flags(
            target,
            "ifort",
            "icc",
            [],
            srcfiles,
            osname="linux",
            sharedobject=sharedobject,
            verbose=verbose,
        )
        line += f"\t\tLDFLAGS ?= {' '.join(tsyslibs)}\n"
        line += "\tendif\n"

    line += "endif\n\n"
    text += line

    return text


def _makedefaults_tasks(fext, cext):
    """Return the windows check and the task functions for makedefaults.

    Returns
    -------
    line : str
        the lines that define the tasks

    """
    # the lines are built one at a time from what every line needs, so
    # the function takes more than the analysis expects
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    # pylint: disable=too-many-locals,too-many-statements
    text = ""
    # check for windows error condition
    line = "# check for Windows error condition\n"
    line += "ifeq ($(detected_OS), Windows)\n"
    if fext is not None:
        line += _makefile_compiler_ifeq("FC", ["ifort", "mpiifort"])
        line += "\t\tWINDOWSERROR = $(FC)\n"
        line += "\tendif\n"
    if cext is not None:
        line += _makefile_compiler_ifeq("CC", ["icl"])
        line += "\t\tWINDOWSERROR = $(CC)\n"
        line += "\tendif\n"
    line += "endif\n\n"
    text += line

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
    text += line

    # close the makedefaults
    return text
