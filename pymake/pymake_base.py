#! /usr/bin/env python
import os
import sys
import traceback
import shutil
import argparse
import datetime

from .pymake import __description__, __version__

from .Popen_wrapper import (
    process_Popen_initialize,
    process_Popen_command,
    process_Popen_stdout,
    process_Popen_communicate,
)
from .compiler_switches import (
    get_osname,
    get_optlevel,
    get_c_flags,
    get_fortran_flags,
    get_linker_flags,
)
from .compiler_language_files import (
    get_ordered_srcfiles,
    get_c_files,
    get_fortran_files,
)

if sys.version_info >= (3, 3):
    from shutil import which
else:
    from distutils.spawn import find_executable as which

# define temporary directories
srcdir_temp = os.path.join(".", "src_temp")
objdir_temp = os.path.join(".", "obj_temp")
moddir_temp = os.path.join(".", "mod_temp")


def parser():
    """Construct the parser and return argument values.

    Parameters
    ----------

    Returns
    -------
    args : list
        command line argument list

    """
    description = __description__
    parser = argparse.ArgumentParser(
        description=description,
        epilog="""Note that the source directory
                                     should not contain any bad or duplicate
                                     source files as all source files in the
                                     source directory will be built and
                                     linked.""",
    )
    parser.add_argument("srcdir", help="Location of source directory")
    parser.add_argument("target", help="Name of target to create")
    parser.add_argument(
        "-fc",
        help="Fortran compiler to use (default is gfortran)",
        default="gfortran",
        choices=["ifort", "mpiifort", "gfortran", "none"],
    )
    parser.add_argument(
        "-cc",
        help="C compiler to use (default is gcc)",
        default="gcc",
        choices=["gcc", "clang", "icc", "mpiicc", "g++", "cl", "none"],
    )
    parser.add_argument(
        "-ar",
        "--arch",
        help="Architecture to use for ifort (default is intel64)",
        default="intel64",
        choices=["ia32", "ia32_intel64", "intel64"],
    )
    parser.add_argument(
        "-mc", "--makeclean", help="Clean files when done", action="store_true"
    )
    parser.add_argument(
        "-dbl", "--double", help="Force double precision", action="store_true"
    )
    parser.add_argument(
        "-dbg", "--debug", help="Create debug version", action="store_true"
    )
    parser.add_argument(
        "-e",
        "--expedite",
        help="""Only compile out of date source files.
                        Clean must not have been used on previous build.
                        Does not work yet for ifort.""",
        action="store_true",
    )
    parser.add_argument(
        "-dr",
        "--dryrun",
        help="""Do not actually compile.  Files will be
                        deleted, if --makeclean is used.
                        Does not work yet for ifort.""",
        action="store_true",
    )
    parser.add_argument(
        "-sd",
        "--subdirs",
        help="""Include source files in srcdir
                        subdirectories.""",
        action="store_true",
    )
    parser.add_argument(
        "-ff",
        "--fflags",
        help="""Additional fortran compiler flags.""",
        default=None,
    )
    parser.add_argument(
        "-cf",
        "--cflags",
        help="""Additional c compiler flags.""",
        default=None,
    )
    parser.add_argument(
        "-sl",
        "--syslibs",
        help="""Linker system libraries.""",
        default=None,
        choices=["-lc", "-lm"],
    )
    parser.add_argument(
        "-mf",
        "--makefile",
        help="""Create a standard makefile.""",
        action="store_true",
    )
    parser.add_argument(
        "-cs",
        "--commonsrc",
        help="""Additional directory with common source files.""",
        default=None,
    )
    parser.add_argument(
        "-ef",
        "--extrafiles",
        help="""List of extra source files to include in the
                        compilation.  extrafiles can be either a list of files
                        or the name of a text file that contains a list of
                        files.""",
        default=None,
    )
    parser.add_argument(
        "-exf",
        "--excludefiles",
        help="""List of extra source files to exclude from the
                        compilation.  excludefiles can be either a list of 
                        files or the name of a text file that contains a list
                        of files.""",
        default=None,
    )
    parser.add_argument(
        "-so",
        "--sharedobject",
        help="Create shared object",
        action="store_false",
        default=False,
    )
    args = parser.parse_args()
    return args


def pymake_initialize(srcdir, target, commonsrc, extrafiles, excludefiles):
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

    Returns
    -------
    None

    """
    # remove the target if it already exists
    try:
        os.remove(target)
    except:
        pass

    # remove srcdir_temp and copy in srcdir
    try:
        shutil.rmtree(srcdir_temp)
    except:
        pass
    shutil.copytree(srcdir, srcdir_temp)

    # copy files from a specified common source directory if
    # commonsrc is not None
    if commonsrc is not None:
        pth = os.path.basename(os.path.normpath(commonsrc))
        pth = os.path.join(srcdir_temp, pth)
        shutil.copytree(commonsrc, pth)

    # if extrafiles is not none, then it is a text file with a list of
    # additional source files that need to be copied into srctemp and
    # compiled.
    files = get_extrafiles(extrafiles)
    if files is None:
        files = []
    for fname in files:
        if not os.path.isfile(fname):
            print("Current working directory: {}".format(os.getcwd()))
            print("Error in extrafiles: {}".format(extrafiles))
            print("Could not find file: {}".format(fname))
            raise Exception()
        dst = os.path.join(srcdir_temp, os.path.basename(fname))
        if os.path.isfile(dst):
            raise Exception(
                "Error with extrafile.  Name conflicts with "
                "an existing source file: {}".format(dst)
            )
        shutil.copy(fname, dst)

    # if exclude is not None, then it is a text file with a list of
    # source files that need to be excluded from srctemp.
    files = get_extrafiles(excludefiles)
    if files is None:
        files = []
    for fname in files:
        if not os.path.isfile(fname):
            print("Current working directory: {}".format(os.getcwd()))
            print("Warning in excludefiles: {}".format(excludefiles))
            print("Could not find file: {}".format(fname))
        else:
            base = None
            tail = True
            while tail:
                fname, tail = os.path.split(fname)
                if base is None:
                    base = tail
                else:
                    base = os.path.join(tail, base)
                dst = os.path.join(srcdir_temp, base)
                if os.path.isfile(dst):
                    os.remove(dst)
                    tail = False

    # if they don't exist, create directories for objects and mods
    if not os.path.exists(objdir_temp):
        os.makedirs(objdir_temp)
    if not os.path.exists(moddir_temp):
        os.makedirs(moddir_temp)

    return


def get_extrafiles(extrafiles):
    """Get.

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
                "or the name of a text file that contains a list"
                "of files."
            )
    return files


def clean(target, intelwin):
    """Cleanup intermediate files. Remove mod and object files, and remove the
    temporary source directory.

    Parameters
    ----------
    target : str
        path for executable to create
    intelwin : bool
        boolean indicating if pymake was used to compile source code on
        Windows using Intel compilers

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
    print("\nCleaning up temporary source, object, and module files...")
    filelist = os.listdir(".")
    delext = [".mod", objext]
    for f in filelist:
        for ext in delext:
            if f.endswith(ext):
                print("    removing...{}".format(f))
                os.remove(f)

    # shared object intermediate files
    print("\nCleaning up intermediate shared object files...")
    delext = [".exp", ".lib"]
    dpth = os.path.dirname(target)
    for f in os.listdir(dpth):
        fpth = os.path.join(dpth, f)
        for ext in delext:
            if fpth.endswith(ext):
                print("    removing...'{}'".format(fpth))
                os.remove(fpth)

    # remove temporary directories
    print("\nCleaning up temporary source, object, and module directories...")
    if os.path.isdir(srcdir_temp):
        shutil.rmtree(srcdir_temp)
    if os.path.isdir(objdir_temp):
        shutil.rmtree(objdir_temp)
    if os.path.isdir(moddir_temp):
        shutil.rmtree(moddir_temp)

    # remove the windows batchfile
    if intelwin:
        os.remove("compile.bat")
    return


def create_openspec():
    """Create new openspec.inc, FILESPEC.INC, and filespec.inc files that uses
    STREAM ACCESS. This is specific to MODFLOW and MT3D based targets. Source
    directories are scanned and files defining file access are replaced.

    Parameters
    ----------

    Returns
    -------
    None

    """
    files = ["openspec.inc", "filespec.inc"]
    dirs = [d[0] for d in os.walk(srcdir_temp)]
    for d in dirs:
        for file in files:
            fpth = os.path.join(d, file)
            if os.path.isfile(fpth):
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


def check_out_of_date(srcfile, objfile):
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


def pymake_compile(
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

    Returns
    -------
    returncode : int
        returncode

    """
    # initialize returncode
    returncode = 0

    # initialize ilink
    ilink = 0

    # set optimization levels
    optlevel = get_optlevel(target, fc, cc, debug, fflags, cflags)

    # get fortran and c compiler switches
    tfflags = get_fortran_flags(
        target, fc, fflags, debug, double, sharedobject=sharedobject
    )
    tcflags = get_c_flags(
        target, cc, cflags, debug, srcfiles, sharedobject=sharedobject
    )

    # get linker flags and syslibs
    lc, tlflags = get_linker_flags(
        target, fc, cc, syslibs, srcfiles, sharedobject=sharedobject
    )

    # clean exe prior to build so that test for exe below can return a
    # non-zero error code
    if os.path.isfile(target):
        print('removing existing target with same name: {}'.format(target))
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
                print("could not remove '{}'".format(batchfile))

        # Create target using a batch file on Windows
        try:
            create_win_batch(
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
            if get_osname() == "win32":
                if ext.lower() != ".dll":
                    target = program_path + ".dll"
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
                cmdlist.append(fc)
                cmdlist.append(optlevel)
                for switch in tfflags:
                    cmdlist.append(switch)

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
                if not check_out_of_date(srcfile, objfile):
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
            process_Popen_command(False, cmdlist)

            # run the command using Popen
            proc = process_Popen_initialize(cmdlist, intelwin)

            # write batch file execution to terminal
            if intelwin:
                process_Popen_stdout(proc)
            # establish communicator to report errors
            else:
                process_Popen_communicate(proc)

            # evaluate return code
            returncode = proc.returncode
            if returncode != 0:
                msg = "compilation failed on '{}'".format(" ".join(cmdlist))
                print(msg)
                break

    # return
    return returncode


def create_win_batch(
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
    # get path to compilervars batch file
    iflist = ["IFORT_COMPILER{}".format(i) for i in range(30, 12, -1)]
    found = False
    for ift in iflist:
        cpvars = os.environ.get(ift)
        if cpvars is not None:
            found = True
            break
    if not found:
        raise Exception("Pymake could not find IFORT compiler.")
    cpvars += os.path.join("bin", "compilervars.bat")
    if not os.path.isfile(cpvars):
        raise Exception("Could not find cpvars: {}".format(cpvars))

    # open the batch file
    f = open(batchfile, "w")

    # write the compilervars batch command to batchfile
    line = "call " + '"' + os.path.normpath(cpvars) + '" ' + arch + "\n"
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


def create_makefile(
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
    # set object extension
    objext = ".o"

    # get list of unique fortran and c/c++ file extensions
    fext = get_fortran_files(srcfiles, extensions=True)
    cext = get_c_files(srcfiles, extensions=True)

    # set exe_name
    exe_name = os.path.splitext(os.path.basename(target))[0]

    # build heading
    heading = (
        "# makefile created on {}\n".format(datetime.datetime.now())
        + "# by pymake (version {}) ".format(__version__)
        + "for the '{}' executable \n".format(exe_name)
    )
    heading += "# using the"
    if fext is not None:
        heading += " '{}' fortran".format(fc)
        if cext is not None:
            heading += " and"
    if cext is not None:
        heading += " '{}' c/c++".format(cc)
    heading += " compiler(s).\n"

    # open makefile
    f = open("makefile", "w")

    # write header
    f.write(heading + "\n")

    #  write include file
    line = "\ninclude ./{}\n\n".format(makedefaults)
    f.write(line)

    # determine the directories with source files
    # source files in sdir and sdir2
    dirs = [d[0].replace("\\", "/") for d in os.walk(srcdir)]
    if srcdir2 is not None:
        dirs2 = [d[0].replace("\\", "/") for d in os.walk(srcdir2)]
        dirs = dirs + dirs2

    # source files in extrafiles
    files = get_extrafiles(extrafiles)
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
    for idx, dir in enumerate(dirs):
        vpaths.append("SOURCEDIR{}".format(idx + 1))
        line = "{}={}\n".format(vpaths[idx], dir)
        f.write(line)
    f.write("\n")

    # write vpath
    f.write("VPATH = \\\n")
    for idx, sd in enumerate(vpaths):
        f.write("${" + "{}".format(sd) + "} ")
        if idx + 1 < len(vpaths):
            f.write("\\")
        f.write("\n")
    f.write("\n")

    # write file extensions
    line = ".SUFFIXES: "
    if fext is not None:
        for ext in fext:
            line += "{} ".format(ext)
    if cext is not None:
        for ext in cext:
            line += "{} ".format(ext)
    line += objext
    f.write("{}\n".format(line))
    f.write("\n")

    f.write("OBJECTS = \\\n")
    for idx, srcfile in enumerate(srcfiles):
        objpth = os.path.splitext(os.path.basename(srcfile))[0] + objext
        f.write("$(OBJDIR)/{}".format(objpth))
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
            f.write("$(OBJDIR)/%{} : %{}\n".format(objext, ext))
            f.write("\t@mkdir -p $(@D)\n")
            line = (
                "\t$(FC) $(OPTLEVEL) $(FFLAGS) -c $< -o $@ "
                + "$(INCSWITCH) $(MODSWITCH)\n"
            )
            f.write("{}\n".format(line))

    if cext is not None:
        for ext in cext:
            f.write("$(OBJDIR)/%{} : %{}\n".format(objext, ext))
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
    line += "BINDIR = {}\n".format(dpth)
    line += "OBJDIR = {}\n".format(objdir_temp)
    line += "MODDIR = {}\n".format(moddir_temp)
    line += "INCSWITCH = -I $(OBJDIR)\n"
    line += "MODSWITCH = -J $(MODDIR)\n\n"
    f.write(line)

    line = "# define program name\n"
    line += "PROGRAM = $(BINDIR)/{}\n\n".format(exe_name)
    f.write(line)

    line = "# define os dependent program name\n"
    line += "ifeq ($(detected_OS), Windows)\n"
    line += "\tPROGRAM = $(BINDIR)/{}.exe\n".format(exe_name)
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

    # optimization level
    optlevel = get_optlevel(target, fc, cc, debug, fflags, cflags)
    line = "# set the optimization level (OPTLEVEL) if not defined\n"
    line += "OPTLEVEL ?= {}\n\n".format(optlevel)
    f.write(line)

    # fortran flags
    if fext is not None:
        line = "# set the fortran flags\n"
        line += "ifeq ($(detected_OS), Windows)\n"
        line += "\tifeq ($(FC), gfortran)\n"
        tfflags = get_fortran_flags(
            target, "gfortran", fflags, debug, double, osname="win32"
        )
        for idx, flag in enumerate(tfflags):
            if "-D_" in flag:
                tfflags[idx] = "$(OS_macro)"
        line += "\t\tFFLAGS ?= {}\n".format(" ".join(tfflags))
        line += "\tendif\n"
        line += "else\n"
        line += "\tifeq ($(FC), gfortran)\n"
        tfflags = get_fortran_flags(
            target, "gfortran", fflags, debug, double, osname="linux"
        )
        for idx, flag in enumerate(tfflags):
            if "-D__" in flag:
                tfflags[idx] = "$(OS_macro)"
        line += "\t\tFFLAGS ?= {}\n".format(" ".join(tfflags))
        line += "\tendif\n"
        line += "\tifeq ($(FC), $(filter $(FC), ifort mpiifort))\n"
        tfflags = get_fortran_flags(
            target, "ifort", fflags, debug, double, osname="linux"
        )
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
        tcflags = get_c_flags(
            target, "gcc", fflags, debug, srcfiles, osname="win32"
        )
        line += "\t\tCFLAGS ?= {}\n".format(" ".join(tcflags))
        line += "\tendif\n"
        line += "\tifeq ($(CC), $(filter $(CC), clang clang++))\n"
        tcflags = get_c_flags(
            target, "clang", fflags, debug, srcfiles, osname="win32"
        )
        line += "\t\tCFLAGS ?= {}\n".format(" ".join(tcflags))
        line += "\tendif\n"
        line += "else\n"
        line += "\tifeq ($(CC), $(filter $(CC), gcc g++))\n"
        tcflags = get_c_flags(
            target, "gcc", fflags, debug, srcfiles, osname="linux"
        )
        line += "\t\tCFLAGS ?= {}\n".format(" ".join(tcflags))
        line += "\tendif\n"
        line += "\tifeq ($(CC), $(filter $(CC), clang clang++))\n"
        tcflags = get_c_flags(
            target, "clang", fflags, debug, srcfiles, osname="linux"
        )
        line += "\t\tCFLAGS ?= {}\n".format(" ".join(tcflags))
        line += "\tendif\n"
        line += "\tifeq ($(CC), $(filter $(CC), icc mpiicc icpc))\n"
        tcflags = get_c_flags(
            target, "icc", fflags, debug, srcfiles, osname="linux"
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
        _, tsyslibs = get_linker_flags(
            target, None, "gcc", syslibs, srcfiles, osname="win32"
        )
        line += "\tifeq ($(CC), $(filter $(CC), gcc g++))\n"
        line += "\t\tLDFLAGS ?= {}\n".format(" ".join(tsyslibs))
        line += "\tendif\n"
        _, tsyslibs = get_linker_flags(
            target, None, "clang", syslibs, srcfiles, osname="win32"
        )
        line += "\tifeq ($(CC), $(filter $(CC), clang clang++))\n"
        line += "\t\tLDFLAGS ?= {}\n".format(" ".join(tsyslibs))
        line += "\tendif\n"
    # fortran compiler used for linking
    else:
        _, tsyslibs = get_linker_flags(
            target, "gfortran", "gcc", syslibs, srcfiles, osname="win32"
        )
        line += "\tifeq ($(FC), $(filter $(FC), gfortran))\n"
        line += "\t\tLDFLAGS ?= {}\n".format(" ".join(tsyslibs))
        line += "\tendif\n"
    # linux and osx
    line += "else\n"
    # c/c++ compiler used for linking
    if fext is None:
        _, tsyslibs = get_linker_flags(
            target, None, "gcc", syslibs, srcfiles, osname="linux"
        )
        line += "\tifeq ($(CC), $(filter $(CC), gcc g++))\n"
        line += "\t\tLDFLAGS ?= {}\n".format(" ".join(tsyslibs))
        line += "\tendif\n"
        _, tsyslibs = get_linker_flags(
            target, None, "clang", syslibs, srcfiles, osname="linux"
        )
        line += "\tifeq ($(CC), $(filter $(CC), clang clang++))\n"
        line += "\t\tLDFLAGS ?= {}\n".format(" ".join(tsyslibs))
        line += "\tendif\n"
    # fortran compiler used for linking
    else:
        # gfortran compiler
        line += "\tifeq ($(FC), gfortran)\n"
        _, tsyslibs = get_linker_flags(
            target, "gfortran", "gcc", syslibs, srcfiles, osname="linux"
        )
        line += "\t\tLDFLAGS ?= {}\n".format(" ".join(tsyslibs))
        line += "\tendif\n"
        # ifort compiler
        line += "\tifeq ($(FC), $(filter $(FC), ifort mpiifort))\n"
        _, tsyslibs = get_linker_flags(
            target, "ifort", "icc", syslibs, srcfiles, osname="linux"
        )
        line += "\t\tLDFLAGS ?= {}\n".format(" ".join(tsyslibs))
        line += "\tendif\n"
    line += "endif\n\n"
    f.write(line)

    # task functions
    line = "# Define task functions\n"
    line += "# Create the bin directory and compile and link the program\n"
    line += "all: makedirs | $(PROGRAM)\n\n"
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
        boolean indicating a shared object (.so or .dll) will be built

    Returns
    -------
    returncode : int
        return code

    """
    # initialize return code
    returncode = 0

    if srcdir is not None and target is not None:

        # set fc and cc to None if they are passed as 'none'
        if fc == "none":
            fc = None
        if cc == "none":
            cc = None
        if fc is None and cc is None:
            msg = (
                "Nothing to do the fortran (-fc) and c/c++ compilers (-cc)"
                + "are both None."
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
        print("\nsource files are in:\n    {}\n".format(srcdir))
        print("executable name to be created:\n    {}\n".format(target))
        if srcdir2 is not None:
            print("additional source files are in:\n     {}\n".format(srcdir2))

        # make sure the path for the target exists
        pth = os.path.dirname(target)
        if pth == "":
            pth = "."
        if not os.path.exists(pth):
            print("creating target path - {}\n".format(pth))
            os.makedirs(pth)

        # initialize
        pymake_initialize(srcdir, target, srcdir2, extrafiles, excludefiles)

        # get ordered list of files to compile
        srcfiles = get_ordered_srcfiles(srcdir_temp, include_subdirs)

        # set intelwin flag to True in compiling on windows with Intel compilers
        intelwin = False
        if get_osname() == "win32":
            if fc is not None:
                if fc in ["ifort", "mpiifort"]:
                    intelwin = True
            if cc is not None:
                if cc in ["cl", "icl"]:
                    intelwin = True

        # update openspec files based on intelwin
        if not intelwin:
            create_openspec()

        # compile the executable
        returncode = pymake_compile(
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
        )

        # create makefile
        if makefile:
            create_makefile(
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
            )

        # clean up temporary files
        if makeclean and returncode == 0:
            clean(target, intelwin)
    else:
        returncode = 1

    return returncode


if __name__ == "__main__":
    # get the arguments
    args = parser()

    # call main -- note that this form allows main to be called
    # from python as a function.
    main(
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
        makefile=args.makefile,
        srcdir2=args.commonsrc,
        extrafiles=args.extrafiles,
    )
