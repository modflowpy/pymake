"""Private functions for setting c/c++ and fortran compiler flags and
appropriate linker flags for defined targets.
"""
import os
import sys

from ._Popen_wrapper import (
    _process_Popen_initialize,
    _process_Popen_command,
    _process_Popen_communicate,
)
from ._compiler_language_files import (
    _get_fortran_files,
    _get_c_files,
    _get_iso_c,
)


def _check_gnu_switch_available(switch, compiler="gfortran", verbose=False):
    """Determine if a specified GNU compiler switch exists. Not all switches
    will be detected, for example '-O2'  adn '-fbounds-check=on'.

    Parameters
    ----------
    switch : str
        compiler switch
    compiler : str
        compiler name, must be gfortran or gcc
    verbose : bool
        boolean for verbose output to terminal

    Returns
    -------
    avail : bool
        boolean indicating if the compiler switch is available

    """
    # test if compiler is valid
    if compiler not in ["gfortran", "gcc"]:
        msg = "compiler must be 'gfortran' or 'gcc'."
        raise ValueError(msg)

    # determine the gfortran command line flags available
    cmdlist = [compiler, "--help", "-v"]

    # Try to get gfortran help.  Return False if any problems.
    try:
        proc = _process_Popen_initialize(cmdlist)
        if verbose:
            _process_Popen_command(False, cmdlist)

        # establish communicator
        _, stdout = _process_Popen_communicate(proc, verbose=verbose)

        # determine if flag exists
        avail = switch in stdout

    except:
        avail = False

    # write a message
    if verbose:
        msg = "  {} switch available: {}".format(switch, avail)
        print(msg)

    return avail


def _get_osname():
    """Return the lower case OS platform name.

    Parameters
    -------

    Returns
    -------
    osname : str
        lower case OS platform name

    """
    osname = sys.platform.lower()
    if osname == "linux2":
        osname = "linux"
    return osname


def _get_base_app_name(value):
    """Remove path and extension from an application name.

    Parameters
    ----------
    value : str
        application name that may include a directory path and extension

    Returns
    -------
    value : str
        application name base name with out directory path and extension

    """
    value = os.path.basename(value)
    if (
        value.endswith(".exe")
        or value.endswith(".dll")
        or value.endswith(".dylib")
        or value.endswith(".so")
    ):
        value = os.path.splitext(value)[0]

    return value


def _get_prepend(compiler, osname):
    """Return the appropriate prepend for a compiler switch for a OS.

    Parameters
    -------
    compiler : str
        compiler name
    osname : str
        lower case OS name

    Returns
    -------
    str : str
        prepend string for a compiler switch for a OS

    """
    if compiler in ["gfortran", "gcc", "g++", "clang"]:
        prepend = "-"
    else:
        if osname in ["linux", "darwin"]:
            prepend = "-"
        else:
            prepend = "/"
    return prepend


def _get_optlevel(
    target, fc, cc, debug, fflags, cflags, osname=None, verbose=False
):
    """Return a compiler optimization switch.

    Parameters
    -------
    target : str
        executable to create
    fc : str
        fortran compiler
    cc : str
        c or cpp compiler
    debug : bool
        flag indicating is a debug executible will be built
    fflags : list
        user provided list of fortran compiler flags
    cflags : list
        user provided list of c or cpp compiler flags
    osname : str
        optional lower case OS name. If not passed it will be determined
        using sys.platform
    verbose : bool
        boolean for verbose output to terminal

    Returns
    -------
    optlevel : str
        compiler optimization switch

    """
    # remove target extension, if necessary
    target = _get_base_app_name(target)

    # get lower case OS string
    if osname is None:
        osname = _get_osname()

    # remove .exe extension from compiler if necessary
    if fc is not None:
        fc = _get_base_app_name(fc)
    if cc is not None:
        cc = _get_base_app_name(cc)

    compiler = None
    if fc is not None:
        compiler = fc
    if compiler is None:
        compiler = cc

    # get - or / to prepend for compiler switches
    prepend = _get_prepend(compiler, osname)

    # set basic optimization level
    if debug:
        if osname == "win32":
            optlevel = "O0"
        else:
            optlevel = "O0"
    else:
        optlevel = "O2"

    # look for optimization levels in fflags
    for flag in fflags:
        if flag[:2] == "-O" or flag == "-fast":
            if not debug:
                optlevel = flag[1:]
            break  # after first optimization (O) flag

    # look for optimization levels in cflags
    for flag in cflags:
        if flag[:2] == "-O":
            if not debug:
                optlevel = flag[1:]
            break  # after first optimization (O) flag

    # reset optlevel with specified flags from setters
    if compiler == fc:
        tval = _set_fflags(target, fc, argv=False, osname=osname)
    else:
        tval = _set_cflags(target, cc, argv=False, osname=osname)

    # look for for optimization levels in compiler flags from setters
    if tval is not None:
        for flag in tval:
            if flag[:2] == "-O":
                if not debug:
                    optlevel = flag[1:]
                break  # after first optimization (O) flag

    # prepend optlevel
    optlevel = prepend + optlevel

    return optlevel


def _get_fortran_flags(
    target,
    fc,
    fflags,
    debug,
    double=False,
    sharedobject=False,
    osname=None,
    verbose=False,
):
    """Return a list of pymake and user specified fortran compiler switches.

    Parameters
    -------
    target : str
        executable to create
    fc : str
        fortran compiler
    fflags : list
        user provided list of fortran compiler flags
    debug : bool
        boolean indicating a debug executable will be built
    double : bool
        boolean indicating a compiler switch will be used to create an
        executable with double precision real variables.
    sharedobject : bool
        boolean indicating a shared object will be built
    osname : str
        optional lower case OS name. If not passed it will be determined
        using sys.platform
    verbose : bool
        boolean for verbose output to terminal

    Returns
    -------
    flags : str
        fortran compiler switches

    """
    flags = []

    # define fortran flags
    if fc is not None:
        # remove .exe extension of necessary
        fc = _get_base_app_name(fc)

        # remove target .exe extension, if necessary
        target = _get_base_app_name(target)

        # get lower case OS string
        if osname is None:
            osname = _get_osname()

        # get - or / to prepend for compiler switches
        prepend = _get_prepend(fc, osname)

        # generate standard fortran flags
        if fc == "gfortran":
            if sharedobject:
                if osname != "win32":
                    flags.append("fPIC")
            else:
                if osname == "win32":
                    flags.append("static")
                if "fPIC" in flags:
                    flags.remove("fPIC")
            flags.append("fbacktrace")
            if debug:
                flags += ["g", "fcheck=all", "fbounds-check", "Wall"]
                if _check_gnu_switch_available("-ffpe-trap", verbose=verbose):
                    flags.append("ffpe-trap=overflow,zero,invalid,denormal")
            else:
                if _check_gnu_switch_available("-ffpe-summary"):
                    flags.append("ffpe-summary=overflow")
                if _check_gnu_switch_available("-ffpe-trap"):
                    flags.append("ffpe-trap=overflow,zero,invalid")
            if double:
                flags += ["fdefault-real-8", "fdefault-double-8"]
            # define the OS macro for gfortran
            os_macro = _get_os_macro(osname)
            if os_macro is not None:
                flags.append(os_macro)
        elif fc in ["ifort", "mpiifort"]:
            if osname == "win32":
                flags += ["heap-arrays:0", "fpe:0", "traceback", "nologo"]
                if debug:
                    flags += ["debug:full", "Zi"]
                if double:
                    flags += ["real-size:64", "double-size:64"]
            else:
                if sharedobject:
                    flags.append("fPIC")
                else:
                    if "fPIC" in flags:
                        flags.remove("fPIC")
                if debug:
                    flags += ["g"]
                flags += ["no-heap-arrays", "fpe0", "traceback"]
                if double:
                    flags += ["r8", "autodouble"]

        # process passed fortran flags - check for flags with a space between
        # the flag and a setting
        for idx, flag in enumerate(fflags[1:]):
            if flag[0] not in ("/", "-"):
                fflags[idx] += " {}".format(flag)
                fflags[idx + 1] = ""

        # Add passed fortran flags - assume that flags have - or / as the
        # first character. fortran flags starting with O are excluded
        for flag in fflags:
            if len(flag) < 1:
                continue
            if flag[1] != "O":
                if flag[1:] not in flags:
                    flags.append(flag[1:])

        # add target specific fortran switches
        tlist = _set_fflags(target, fc=fc, argv=False, osname=osname)
        if tlist is not None:
            for flag in tlist:
                if flag[1] != "O":
                    if flag[1:] not in flags:
                        flags.append(flag[1:])

        # add prepend to compiler flags
        for idx, flag in enumerate(flags):
            flags[idx] = prepend + flag

    return flags


def _get_c_flags(
    target,
    cc,
    cflags,
    debug,
    srcfiles=None,
    sharedobject=False,
    osname=None,
    verbose=False,
):
    """Return a list of standard and user specified c/c++ compiler switches.

    Parameters
    -------
    target : str
        executable to create
    cc : str
        c or cpp compiler
    cflags : list
        user provided list of c or cpp compiler flags
    debug : bool
        flag indicating a debug executable will be built
    srcfiles : list
        list of source file names
    sharedobject : bool
        boolean indicating a shared object will be built
    osname : str
        optional lower case OS name. If not passed it will be determined
        using sys.platform
    verbose : bool
        boolean for verbose output to terminal

    Returns
    -------
    flags : str
        c or cpp compiler switches

    """
    flags = []

    # define c flags
    if cc is not None:
        # remove .exe extension of necessary
        cc = _get_base_app_name(cc)

        # remove target .exe extension, if necessary
        target = _get_base_app_name(target)

        # get lower case OS string
        if osname is None:
            osname = _get_osname()

        # get - or / to prepend for compiler switches
        prepend = _get_prepend(cc, osname)

        # generate c flags
        if cc in ["gcc", "g++"]:
            if sharedobject:
                if osname != "win32":
                    flags.append("fPIC")
            else:
                if osname == "win32":
                    flags.append("static")
                if "fPIC" in flags:
                    flags.remove("fPIC")
            if debug:
                flags += ["g"]
                if _check_gnu_switch_available(
                    "-Wall", compiler="gcc", verbose=verbose
                ):
                    flags.append("Wall")
            else:
                pass
        elif cc in ["clang", "clang++"]:
            if sharedobject:
                msg = "shared library not implement fo clang"
                raise NotImplementedError(msg)
            if debug:
                flags += ["g"]
                if _check_gnu_switch_available(
                    "-Wall", compiler="clang", verbose=verbose
                ):
                    flags.append("Wall")
            else:
                pass
        elif cc in ["icc", "icpc", "mpiicc", "mpiicpc", "icl", "cl"]:
            if osname == "win32":
                if cc in ["icl", "cl"]:
                    flags += ["nologo"]
                if debug:
                    flags.append("/debug:full")
            else:
                if sharedobject:
                    flags.append("fpic")
                else:
                    if "fpic" in flags:
                        flags.remove("fpic")

                if debug:
                    flags += ["debug full"]
        elif cc in ["cl"]:
            if osname == "win32":
                if debug:
                    flags.append("Zi")

        # Add -D-UF flag for C code if ISO_C_BINDING is not used in Fortran
        # code that is linked to C/C++ code. Only needed if there are
        # any fortran files. -D_UF defines UNIX naming conventions for
        # mixed language compilation.
        if srcfiles is not None:
            ffiles = _get_fortran_files(srcfiles)
            cfiles = _get_c_files(srcfiles)
            if ffiles is not None:
                iso_c_check = True
                if osname == "win32":
                    if cc in ["icl", "cl"]:
                        iso_c_check = False
                if iso_c_check:
                    use_iso_c = _get_iso_c(ffiles)
                    if not use_iso_c and cfiles is not None:
                        flags.append("D_UF")

        # process passed c flags - check for flags with a space between
        # the flag and a setting
        for idx, flag in enumerate(cflags[1:]):
            if flag[0] not in ("/", "-"):
                cflags[idx] += " {}".format(flag)
                cflags[idx + 1] = ""

        # add passed c flags - assume that flags have - or / as the
        # first character. c flags starting with O are excluded
        for flag in cflags:
            if len(flag) < 1:
                continue
            if flag[1] != "O":
                if flag[1:] not in flags:
                    flags.append(flag[1:])

        # add target specific c/c++ switches
        tlist = _set_cflags(target, cc=cc, argv=False, osname=osname)
        if tlist is not None:
            for flag in tlist:
                if flag[1] != "O":
                    if flag[1:] not in flags:
                        flags.append(flag[1:])

        # add prepend to compiler flags
        for idx, flag in enumerate(flags):
            flags[idx] = prepend + flag

    return flags


def _get_linker_flags(
    target,
    fc,
    cc,
    syslibs,
    srcfiles,
    sharedobject=False,
    osname=None,
    verbose=False,
):
    """Return the compiler to use for linking and a list of pymake and user
    specified linker switches (syslibs).

    Parameters
    -------
    target : str
        executable to create
    fc : str
        fortran compiler
    cc : str
        c or cpp compiler
    syslibs : list
        user provided list of linker flags and libraries
    srcfiles : list
        list of source file names
    sharedobject : bool
        boolean indicating a shared object will be built
    osname : str
        optional lower case OS name. If not passed it will be determined
        using sys.platform
    verbose : bool
        boolean for verbose output to terminal

    Returns
    -------
    compiler : str
        linker compiler
    flags : list
        list of linker switches
    syslibs : list
        list of syslibs for the linker

    """
    # get list of unique fortran and c/c++ file extensions
    fext = _get_fortran_files(srcfiles, extensions=True)

    # remove .exe extension of necessary
    if fc is not None:
        fc = _get_base_app_name(fc)
    if cc is not None:
        cc = _get_base_app_name(cc)

    # set linker compiler
    compiler = None
    if len(srcfiles) < 1:
        if fc is not None:
            compiler = fc
    else:
        if fext is not None:
            compiler = fc
    if compiler is None:
        compiler = cc

    # remove target .exe extension, if necessary
    target = _get_base_app_name(target)

    # get lower case OS string
    if osname is None:
        osname = _get_osname()

    # get - or / to prepend for compiler switches
    prepend = _get_prepend(compiler, osname)

    # set outgoing syslibs
    syslibs_out = []

    # add option to statically link intel provided libraries on osx and linux
    if sharedobject:
        if osname in (
            "darwin",
            "linux",
        ):
            if compiler == fc:
                if fc in (
                    "ifort",
                    "mpiifort",
                ):
                    syslibs_out.append("static-intel")

    # add linker switch for a shared object
    if sharedobject:
        gnu_compiler = True
        if compiler == fc:
            if fc in (
                "ifort",
                "mpiifort",
            ):
                gnu_compiler = False
        else:
            if cc in (
                "icc",
                "mpiicc",
                "icl",
                "cl",
            ):
                gnu_compiler = False
        if osname == "win32":
            if gnu_compiler:
                copt = "shared"
            else:
                copt = "dll"
        else:
            if osname == "darwin":
                copt = "dynamiclib"
            else:
                copt = "shared"
        syslibs_out.append(copt)
    # add static link flags for GNU compilers
    else:
        if "shared" in syslibs_out:
            syslibs_out.remove("shared")
        if "dynamiclib" in syslibs_out:
            syslibs_out.remove("dynamiclib")
        if "dll" in syslibs_out:
            syslibs_out.remove("dll")
        isstatic = False
        isgfortran = False
        if osname == "win32":
            if compiler == fc and fc in ("gfortran",):
                isstatic = True
                isgfortran = True
            if not isstatic:
                if compiler == cc and cc in (
                    "gcc",
                    "g++",
                ):
                    isstatic = True
        if isstatic:
            syslibs_out.append("static")
            if isgfortran:
                syslibs_out.append("static-libgfortran")
            syslibs_out.append("static-libgcc")
            syslibs_out.append("static-libstdc++")
            syslibs_out.append("lm")

    # add -nologo switch for compiling on windows with intel compilers
    if osname == "win32":
        addswitch = False
        if compiler == fc:
            if fc in (
                "ifort",
                "mpiifort",
            ):
                addswitch = True
        else:
            if cc in (
                "icl",
                "cl",
            ):
                addswitch = True
        if addswitch:
            syslibs_out.append("nologo")

    # process passed syslibs switches - check for switches with a space between
    # the switch and a setting
    for idx, flag in enumerate(syslibs[1:]):
        if flag[0] not in ("/", "-"):
            syslibs[idx] += " {}".format(flag)
            syslibs[idx + 1] = ""

    # add passed syslibs switches - assume that flags have - or / as the
    # first character.
    for switch in syslibs:
        if len(switch) < 1:
            continue
        if switch[1:] not in syslibs_out:
            syslibs_out.append(switch[1:])

    # add target specific linker (syslib) switches
    tlist = _set_syslibs(target, fc=fc, cc=cc, argv=False, osname=osname)
    if len(tlist) > 0:
        for switch in tlist:
            if switch[1:] not in syslibs_out:
                syslibs_out.append(switch[1:])

    # add prepend to syslibs flags
    for idx, switch in enumerate(syslibs_out):
        syslibs_out[idx] = prepend + switch

    return compiler, syslibs_out


def _set_fflags(target, fc="gfortran", argv=True, osname=None, verbose=False):
    """Set appropriate fortran compiler flags based on target.

    Parameters
    ----------
    target : str
        target to build
    fc : str
        fortran compiler (default is gfortran)
    argv : bool
        boolean indicating if additional fortran flags can be provided using
        command line arguments (default is True)
    osname : str
        optional lower case OS name. If not passed it will be determined
        using sys.platform
    verbose : bool
        boolean for verbose output to terminal

    Returns
    -------
    fflags : str
        fortran compiler flags. Default is None

    """
    fflags = None

    if fc is not None:
        fflags = []
        # get lower case OS string
        if osname is None:
            osname = _get_osname()

        # remove target .exe extension, if necessary
        target = _get_base_app_name(target)

        # remove .exe extension if necessary
        fc = _get_base_app_name(fc)

        if target == "mp7":
            if fc == "gfortran":
                fflags.append("-ffree-line-length-512")
        elif target == "gsflow":
            if fc == "ifort":
                if osname == "win32":
                    fflags += [
                        "-fp:source",
                        "-names:lowercase",
                        "-assume:underscore",
                    ]
                else:
                    pass
            elif fc == "gfortran":
                fflags += ["-O1", "-fno-second-underscore"]
                opt = "-fallow-argument-mismatch"
                if _check_gnu_switch_available(
                    opt, compiler=fc, verbose=verbose
                ):
                    fflags += [
                        opt,
                    ]
        elif target in (
            "mf2000",
            "mt3dms",
            "swtv4",
        ):
            if fc == "gfortran":
                opt = "-fallow-argument-mismatch"
                if _check_gnu_switch_available(
                    opt, compiler=fc, verbose=verbose
                ):
                    fflags += [
                        opt,
                    ]
        elif target in (
            "mf6",
            "libmf6",
            "zbud6",
        ):
            if fc == "gfortran":
                fflags += [
                    "-Wtabs",
                    "-Wline-truncation",
                    "-Wunused-label",
                    "-Wunused-variable",
                    "-pedantic",
                    "-std=f2008",
                    "-Wcharacter-truncation",
                ]

        # add additional fflags from the command line
        if argv:
            for idx, arg in enumerate(sys.argv):
                if "--fflags" in arg.lower():
                    s = sys.argv[idx + 1]
                    delim = " -"
                    if " /" in s:
                        delim = " /"
                    fflags += s.split(delim)

        # write fortran flags
        if len(fflags) < 1:
            fflags = None
        else:
            if verbose:
                msg = (
                    "{} fortran code ".format(target)
                    + "will be built with the following predefined flags:\n"
                )
                msg += "    {}\n".format(" ".join(fflags))
                print(msg)

    return fflags


def _set_cflags(target, cc="gcc", argv=True, osname=None, verbose=False):
    """Set appropriate c compiler flags based on target.

    Parameters
    ----------
    target : str
        target to build
    cc : str
        c compiler (default is gcc)
    argv : bool
        boolean indicating if additional c compiler flags can be provided
        using command line arguments
    osname : str
        optional lower case OS name. If not passed it will be determined
        using sys.platform
    verbose : bool
        boolean for verbose output to terminal

    Returns
    -------
    cflags : str
        c compiler flags. Default is None

    """
    cflags = None

    if cc is not None:
        cflags = []
        # get lower case OS string
        if osname is None:
            osname = _get_osname()

        # remove target .exe extension, if necessary
        target = _get_base_app_name(target)

        # remove .exe extension of necessary
        cc = _get_base_app_name(cc)

        if target == "triangle":
            if osname in ["linux", "darwin"]:
                if cc.startswith("g"):
                    cflags += ["-lm"]
            else:
                cflags += ["-DNO_TIMER"]
        elif target == "gsflow":
            if cc in ["icc", "icpl", "icl"]:
                if osname == "win32":
                    cflags += ["-D_CRT_SECURE_NO_WARNINGS"]
                else:
                    cflags += ["-D_UF"]
            elif cc == "gcc":
                cflags += ["-O1"]

        # add additional cflags from the command line
        if argv:
            for idx, arg in enumerate(sys.argv):
                if "--cflags" in arg.lower():
                    s = sys.argv[idx + 1]
                    delim = " -"
                    if " /" in s:
                        delim = " /"
                    cflags += s.split(delim)

        # write c/c++ flags
        if len(cflags) < 1:
            cflags = None
        else:
            if verbose:
                msg = (
                    "{} c/c++ code ".format(target)
                    + "will be built with the following predefined flags:\n"
                )
                msg += "    {}\n".format(" ".join(cflags))
                print(msg)

    return cflags


def _set_syslibs(
    target, fc="gfortran", cc="gcc", argv=True, osname=None, verbose=False
):
    """Set appropriate linker flags (syslib) based on target.

    Parameters
    ----------
    target : str
        target to build
    fc : str
        fortran compiler (default is gfortran)
    cc : str
        c compiler (default is gcc)
    argv : bool
        boolean indicating if additional syslibs can be provided using
        command line arguments (default is True)
    osname : str
        optional lower case OS name. If not passed it will be determined
        using sys.platform
    verbose : bool
        boolean for verbose output to terminal

    Returns
    -------
    syslibs : str
        linker flags. Default is None

    """
    # get lower case OS string
    if osname is None:
        osname = _get_osname()

    # remove target .exe extension, if necessary
    target = _get_base_app_name(target)

    # remove .exe extension of necessary
    if fc is not None:
        fc = _get_base_app_name(fc)
    if cc is not None:
        cc = _get_base_app_name(cc)

    # initialize syslibs
    syslibs = []

    # determine if default syslibs will be defined
    default_syslibs = True
    if osname == "win32":
        if fc is not None:
            if fc in ["ifort", "gfortran"]:
                default_syslibs = False
        if default_syslibs:
            if cc is not None:
                if cc in ["cl", "icl", "gcc", "g++"]:
                    default_syslibs = False

    if verbose:
        print("\nosname:  ", osname)
        print("fc:      ", fc)
        print("cc:      ", cc)
        print("default: {}\n".format(default_syslibs))

    # set default syslibs
    if default_syslibs:
        syslibs.append("-lc")

    # add additional syslibs for select programs
    if target == "triangle":
        if osname in ["linux", "darwin"]:
            if fc is None:
                lfc = True
            else:
                lfc = fc.startswith("g")
            lcc = False
            if cc in ["gcc", "g++", "clang", "clang++"]:
                lcc = True
            if lfc and lcc:
                syslibs += ["-lm"]
    elif target == "gsflow":
        if "win32" not in osname:
            if "ifort" in fc:
                syslibs += ["-nofor_main"]

    # add additional syslibs from the command line
    if argv:
        for idx, arg in enumerate(sys.argv):
            if "--syslibs" in arg.lower():
                s = sys.argv[idx + 1]
                delim = " -"
                if " /" in s:
                    delim = " /"
                syslibs += s.split(delim)

    # write syslibs
    if verbose:
        msg = "{} will use the following predefined syslibs:\n".format(target)
        msg += "    '{}'\n".format(" ".join(syslibs))
        print(msg)

    return syslibs


# hidden functions
def _get_os_macro(osname=None):
    """Get OS macro

    Parameters
    ----------
    osname : str
        optional lower case OS name. If not passed it will be determined
        using sys.platform

    Returns
    -------
    os_macro : str
        os macro flag

    """
    os_macro_dict = {
        "win32": "D_WIN32",
        "darwin": "D__APPLE__",
        "linux": "D__linux__",
        "bsd": "D__unix__",
    }
    # get lower case OS string
    if osname is None:
        osname = _get_osname()
    if osname in os_macro_dict.keys():
        os_macro = os_macro_dict[osname]
    else:
        os_macro = None
    return os_macro
