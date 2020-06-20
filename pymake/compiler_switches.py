import os
import sys
import platform

from .Popen_wrapper import process_Popen_initialize, process_Popen_command, \
    process_Popen_communicate
from .compiler_language_files import get_fortran_files, get_c_files, get_iso_c


def check_gnu_switch_available(switch, compiler='gfortran'):
    """Determine if a specified GNU compiler switch exists. Not all switches
    will be detected, for example '-O2'  adn '-fbounds-check=on'.

    Parameters
    ----------
    switch : str
        compiler switch
    compiler : str
        compiler name, must be gfortran or gcc

    Returns
    -------
    avail : bool
        boolean indicating if the compiler switch is available
    """
    # test if compiler is valid
    if compiler not in ['gfortran', 'gcc']:
        msg = "compiler must be 'gfortran' or 'gcc'."
        raise ValueError(msg)

    # determine the gfortran command line flags available
    cmdlist = [compiler, '--help', '-v']
    # proc = Popen(cmdlist, stdout=PIPE, stderr=PIPE, shell=False)
    proc = process_Popen_initialize(cmdlist)
    process_Popen_command(False, cmdlist)

    # establish communicator
    stdout, _ = process_Popen_communicate(proc, verbose=False)

    # determine if flag exists
    avail = switch in stdout

    # write a message
    msg = '  {} switch available: {}'.format(switch, avail)
    print(msg)

    return avail


def get_osname():
    """Return the lower case OS platform name.

    Parameters
    -------

    Returns
    -------
    osname : str
        lower case OS platform name
    """
    osname = sys.platform.lower()
    if osname == 'linux2':
        osname = 'linux'
    return osname


def get_prepend(compiler, osname):
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
    if compiler in ['gfortran', 'gcc', 'g++', 'clang']:
        prepend = '-'
    else:
        if osname in ['linux', 'darwin']:
            prepend = '-'
        else:
            prepend = '/'
    return prepend


def get_optlevel(target, fc, cc, debug, fflags, cflags, osname=None):
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

    Returns
    -------
    optlevel : str
        compiler optimization switch
    """
    # remove target .exe extension, if necessary
    target = os.path.basename(target)
    if '.exe' in target.lower():
        target = target[:-4]

    # get lower case OS string
    if osname is None:
        osname = get_osname()

    # remove .exe extension from compiler if necessary
    if fc is not None:
        if '.exe' in fc.lower():
            fc = fc[:-4]
    if cc is not None:
        if '.exe' in cc.lower():
            cc = cc[:-4]

    compiler = None
    if fc is not None:
        compiler = fc
    if compiler is None:
        compiler = cc

    # get - or / to prepend for compiler switches
    prepend = get_prepend(compiler, osname)

    # set basic optimization level
    if debug:
        if osname == 'win32':
            optlevel = 'Od'
        else:
            optlevel = 'O0'
    else:
        optlevel = 'O2'

    # look for optimization levels in fflags
    for flag in fflags:
        if flag[:2] == '-O' or flag == '-fast':
            if not debug:
                optlevel = flag[1:]
            break  # after first optimization (O) flag

    # look for optimization levels in cflags
    for flag in cflags:
        if flag[:2] == '-O':
            if not debug:
                optlevel = flag[1:]
            break  # after first optimization (O) flag

    # reset optlevel with specified flags from setters
    if compiler == fc:
        tval = set_fflags(target, fc, argv=False, osname=osname)
    else:
        tval = set_cflags(target, cc, argv=False, osname=osname)

    # look for for optimization levels in compiler flags from setters
    if tval is not None:
        for flag in tval:
            if flag[:2] == '-O':
                if not debug:
                    optlevel = flag[1:]
                break  # after first optimization (O) flag

    # prepend optlevel
    optlevel = prepend + optlevel

    return optlevel


def get_fortran_flags(target, fc, fflags, debug, double=False,
                      sharedobject=False, osname=None):
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
        boolean indicating a shared object (.so or .dll) will be built
    osname : str
        optional lower case OS name. If not passed it will be determined
        using sys.platform

    Returns
    -------
    flags : str
        fortran compiler switches
    """
    flags = []

    # define fortran flags
    if fc is not None:
        # remove .exe extension of necessary
        if '.exe' in fc.lower():
            fc = fc[:-4]

        # remove target .exe extension, if necessary
        target = os.path.basename(target)
        if '.exe' in target.lower():
            target = target[:-4]

        # get lower case OS string
        if osname is None:
            osname = get_osname()

        # get - or / to prepend for compiler switches
        prepend = get_prepend(fc, osname)

        # generate standard fortran flags
        if fc == 'gfortran':
            if sharedobject:
                flags.append('fPIC')
            else:
                flags.append('Bstatic')
            flags.append('fbacktrace')
            # if osname == 'win32':
            #     flags.append('Bstatic')
            if debug:
                flags += ['g', 'fcheck=all', 'fbounds-check', 'Wall']
                if check_gnu_switch_available('-ffpe-trap'):
                    flags.append('ffpe-trap=overflow,zero,invalid,denormal')
            else:
                if check_gnu_switch_available('-ffpe-summary'):
                    flags.append('ffpe-summary=overflow')
                if check_gnu_switch_available('-ffpe-trap'):
                    flags.append('ffpe-trap=overflow,zero,invalid')
            if double:
                flags += ['fdefault-real-8', 'fdefault-double-8']
            # define the OS macro for gfortran
            if osname == 'win32':
                os_macro = 'D_WIN32'
            elif osname == 'darwin':
                os_macro = 'D__APPLE__'
            elif 'linux' in osname:
                os_macro = 'D__linux__'
            elif 'bsd' in osname:
                os_macro = 'D__unix__'
            else:
                os_macro = None
            if os_macro is not None:
                flags.append(os_macro)
        elif fc in ['ifort', 'mpiifort']:
            if osname == 'win32':
                flags += ['heap-arrays:0', 'fpe:0', 'traceback', 'nologo']
                if debug:
                    flags += ['debug:full', 'Zi']
                if double:
                    flags += ['real-size:64', 'double-size:64']
            else:
                if sharedobject:
                    flags.append('fPIC')
                if debug:
                    flags += ['g']
                flags += ['no-heap-arrays', 'fpe0', 'traceback']
                if double:
                    flags += ['real-size 64', 'double-size 64']

        # Add passed fortran flags - assume that flags have - or / as the
        # first character. fortran flags starting with O are excluded
        for flag in fflags:
            if flag[1] != 'O':
                if flag[1:] not in flags:
                    flags.append(flag[1:])

        # add target specific fortran switches
        tlist = set_fflags(target, fc=fc, argv=False, osname=osname)
        if tlist is not None:
            for flag in tlist:
                if flag[1] != 'O':
                    if flag[1:] not in flags:
                        flags.append(flag[1:])

        # add prepend to compiler flags
        for idx, flag in enumerate(flags):
            flags[idx] = prepend + flag

    return flags


def get_c_flags(target, cc, cflags, debug, srcfiles=None,
                sharedobject=False, osname=None):
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
        boolean indicating a shared object (.so or .dll) will be built
    osname : str
        optional lower case OS name. If not passed it will be determined
        using sys.platform

    Returns
    -------
    flags : str
        c or cpp compiler switches
    """
    flags = []

    # define c flags
    if cc is not None:
        # remove .exe extension of necessary
        if '.exe' in cc.lower():
            cc = cc[:-4]

        # remove target .exe extension, if necessary
        target = os.path.basename(target)
        if '.exe' in target.lower():
            target = target[:-4]

        # get lower case OS string
        if osname is None:
            osname = get_osname()

        # get - or / to prepend for compiler switches
        prepend = get_prepend(cc, osname)

        # generate c flags
        if cc in ['gcc', 'g++']:
            if sharedobject:
                flags.append('fPIC')
            flags.append('Bstatic')
            if debug:
                flags += ['g']
                if check_gnu_switch_available('-Wall', compiler='gcc'):
                    flags.append('Wall')
            else:
                pass
        elif cc in ['clang', 'clang++']:
            if sharedobject:
                msg = 'shared library not implement fo clang'
                raise NotImplementedError(msg)
            if debug:
                flags += ['g']
                if check_gnu_switch_available('-Wall', compiler='clang'):
                    flags.append('Wall')
            else:
                pass
        elif cc in ['icc', 'icpc', 'mpiicc', 'mpiicpc', 'icl']:
            if osname == 'win32':
                if cc == 'icl':
                    flags += ['nologo']
                if debug:
                    flags.append('/debug:full')
            else:
                if sharedobject:
                    flags.append('fpic')
                if debug:
                    flags += ['debug full']
        elif cc in ['cl']:
            if osname == 'win32':
                if debug:
                    flags.append('Zi')

        # Add -D-UF flag for C code if ISO_C_BINDING is not used in Fortran
        # code that is linked to C/C++ code. Only needed if there are
        # any fortran files. -D_UF defines UNIX naming conventions for
        # mixed language compilation.
        if srcfiles is not None:
            ffiles = get_fortran_files(srcfiles)
            cfiles = get_c_files(srcfiles)
            if ffiles is not None:
                use_iso_c = get_iso_c(ffiles)
                if not use_iso_c and cfiles is not None:
                    flags.append('D_UF')

        # add passed c flags - assume that flags have - or / as the
        # first character. c flags starting with O are excluded
        for flag in cflags:
            if flag[1] != 'O':
                if flag[1:] not in flags:
                    flags.append(flag[1:])

        # add target specific c/c++ switches
        tlist = set_cflags(target, cc=cc, argv=False, osname=osname)
        if tlist is not None:
            for flag in tlist:
                if flag[1] != 'O':
                    if flag[1:] not in flags:
                        flags.append(flag[1:])

        # add prepend to compiler flags
        for idx, flag in enumerate(flags):
            flags[idx] = prepend + flag

    return flags


def get_linker_flags(target, fc, cc, syslibs, srcfiles,
                     sharedobject=False, osname=None):
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
        boolean indicating a shared object (.so or .dll) will be built
    osname : str
        optional lower case OS name. If not passed it will be determined
        using sys.platform

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
    fext = get_fortran_files(srcfiles, extensions=True)
    cext = get_c_files(srcfiles, extensions=True)

    # set linker compiler
    compiler = None
    if fext is not None:
        compiler = fc
    if compiler is None:
        compiler = cc

    # remove compiler .exe extension, if necessary
    if '.exe' in compiler.lower():
        compiler = compiler[:-4]

    # remove target .exe extension, if necessary
    target = os.path.basename(target)
    if '.exe' in target.lower():
        target = target[:-4]

    # get lower case OS string
    if osname is None:
        osname = get_osname()

    # get - or / to prepend for compiler switches
    prepend = get_prepend(compiler, osname)

    # set outgoing syslibs
    syslibs_out = []

    # add linker switch for a shared object
    if sharedobject:
        if osname == 'darwin':
            copt = 'dynamiclib'
        else:
            copt = 'shared'
        syslibs_out.append(copt)
    # add static link flags for GNU compilers
    else:
        if fext is not None and fc in ['gfortran']:
            syslibs_out.append('static-libgfortran')
        if cext is not None and cc in ['gcc', 'g++']:
            syslibs_out.append('static-libgcc')
        if len(syslibs_out) > 0:
            syslibs_out.append('lm')

    # add -nologo switch for compiling on windows with intel compilers
    if osname == 'win32':
        addswitch = False
        if fext is not None:
            if fc in ['ifort', 'mpiifort']:
                addswitch = True
        else:
            if cc in ['icl']:
                addswitch = True
        if addswitch:
            syslibs_out.append('nologo')

    # add passed syslibs switches - assume that flags have - or / as the
    # first character.
    for switch in syslibs:
        if switch[1:] not in syslibs_out:
            syslibs_out.append(switch[1:])

    # add target specific linker (syslib) switches
    tlist = set_syslibs(target, fc=fc, cc=cc, argv=False, osname=osname)
    if len(tlist) > 0:
        for switch in tlist:
            if switch[1:] not in syslibs_out:
                syslibs_out.append(switch[1:])

    # add prepend to syslibs flags
    for idx, switch in enumerate(syslibs_out):
        syslibs_out[idx] = prepend + switch

    return compiler, syslibs_out


def set_compiler(target):
    """Set fortran and c compilers based on --ifort, --mpiifort, --icc, --cl,
    clang++, and --clang command line arguments.

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
    for arg in sys.argv:
        if arg.lower() == '--ifort' and fc is not None:
            fc = 'ifort'
        elif arg.lower() == '--icc':
            cc = 'icc'
        elif arg.lower() == '--icpc':
            cc = 'icpc'
        elif arg.lower() == '--cl':
            cc = 'cl'
        elif arg.lower() == '--icl':
            cc = 'icl'
        elif arg.lower() == '--clang':
            cc = 'clang'
        elif arg.lower() == '--clang++':
            cc = 'clang++'

    # reset cc for gridgen if it is specified as 'clang'
    if target == 'gridgen':
        if cc == 'clang':
            cc = 'clang++'
        elif cc == 'icc':
            cc = 'icpc'

    msg = '{} fortran code will be built with "{}".\n'.format(target, fc)
    msg += '{} c/c++ code will be built with "{}".\n'.format(target, cc)
    print(msg)

    return fc, cc


def set_fflags(target, fc='gfortran', argv=True, osname=None):
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
            osname = get_osname()

        # remove target .exe extension, if necessary
        target = os.path.basename(target)
        if '.exe' in target.lower():
            target = target[:-4]

        # remove .exe extension if necessary
        if '.exe' in fc.lower():
            fc = fc[:-4]

        if target == 'mp7':
            if fc == 'gfortran':
                fflags.append('-ffree-line-length-512')
        elif target == 'gsflow':
            if fc == 'ifort':
                if osname == 'win32':
                    fflags += ['-fp:source', '-names:lowercase',
                               '-assume:underscore']
                else:
                    # fflags.append('-fp-model source')
                    pass
            elif fc == 'gfortran':
                fflags += ['-O1', '-fno-second-underscore']

        # add additional fflags from the command line
        if argv:
            for idx, arg in enumerate(sys.argv):
                if '--fflags' in arg.lower():
                    s = sys.argv[idx + 1]
                    delim = ' -'
                    if ' /' in s:
                        delim = ' /'
                    fflags += s.split(delim)

        # write fortran flags
        if len(fflags) > 0:
            msg = '{} fortran code '.format(target) + \
                  'will be built with the following predefined flags:\n'
            msg += '    {}\n'.format(' '.join(fflags))
            print(msg)
        else:
            fflags = None

    return fflags


def set_cflags(target, cc='gcc', argv=True, osname=None):
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
            osname = get_osname()

        # remove target .exe extension, if necessary
        target = os.path.basename(target)
        if '.exe' in target.lower():
            target = target[:-4]

        # remove .exe extension of necessary
        if '.exe' in cc.lower():
            cc = cc[:-4]

        if target == 'triangle':
            if osname in ['linux', 'darwin']:
                if cc.startswith('g'):
                    cflags += ['-lm']
            else:
                cflags += ['-DNO_TIMER']
        elif target == 'gsflow':
            if cc in ['icc', 'icpl', 'icl']:
                if osname == 'win32':
                    cflags += ['-D_CRT_SECURE_NO_WARNINGS']
                else:
                    cflags += ['-D_UF']
            elif cc == 'gcc':
                cflags += ['-O1']

        # add additional cflags from the command line
        if argv:
            for idx, arg in enumerate(sys.argv):
                if '--cflags' in arg.lower():
                    s = sys.argv[idx + 1]
                    delim = ' -'
                    if ' /' in s:
                        delim = ' /'
                    cflags += s.split(delim)

        # write c/c++ flags
        if len(cflags) > 0:
            msg = '{} c/c++ code '.format(target) + \
                  'will be built with the following predefined flags:\n'
            msg += '    {}\n'.format(' '.join(cflags))
            print(msg)
        else:
            cflags = None

    return cflags


def set_syslibs(target, fc='gfortran', cc='gcc', argv=True, osname=None):
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

    Returns
    -------
    syslibs : str
        linker flags. Default is None
    """
    # get lower case OS string
    if osname is None:
        osname = get_osname()

    # remove target .exe extension, if necessary
    target = os.path.basename(target)
    if '.exe' in target.lower():
        target = target[:-4]

    # initialize syslibs
    syslibs = []

    # determine if default syslibs will be defined
    default_syslibs = True
    if osname == 'win32':
        if fc is not None:
            if fc in ['ifort', 'gfortran']:
                default_syslibs = False
        if default_syslibs:
            if cc is not None:
                if cc in ['cl', 'icl', 'gcc', 'g++']:
                    default_syslibs = False

    # set default syslibs
    if default_syslibs:
        syslibs.append('-lc')

    # add additional syslibs for select programs
    if target == 'triangle':
        if osname in ['linux', 'darwin']:
            if fc is None:
                lfc = True
            else:
                lfc = fc.startswith('g')
            lcc = False
            if cc in ['gcc', 'g++', 'clang', 'clang++']:
                lcc = True
            if lfc and lcc:
                syslibs += ['-lm']
    elif target == 'gsflow':
        if 'win32' not in osname:
            if 'ifort' in fc:
                syslibs += ['-nofor_main']

    # add additional syslibs from the command line
    if argv:
        for idx, arg in enumerate(sys.argv):
            if '--syslibs' in arg.lower():
                s = sys.argv[idx + 1]
                delim = ' -'
                if ' /' in s:
                    delim = ' /'
                syslibs += s.split(delim)

    # write syslibs
    msg = '{} will use the following predefined syslibs:\n'.format(target)
    msg += '    {}\n'.format(' '.join(syslibs))
    print(msg)

    return syslibs


def set_debug(target):
    """Set boolean that defines if the target should be compiled with debug
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
    for arg in sys.argv:
        if arg.lower() == '-dbg' or arg.lower() == '--debug':
            debug = True
            break

    # write a message
    if debug:
        comptype = 'debug'
    else:
        comptype = 'release'
    msg = '{} will be built as a "{}" application.\n'.format(target, comptype)
    print(msg)

    return debug


def set_arch(target):
    """Set architecture to compile target for based on --ia32 command line
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
    msg = '{} will be built for "{}" architecture.\n'.format(target, arch)
    print(msg)

    return arch
