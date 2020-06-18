#! /usr/bin/env python
"""Make a binary executable for a FORTRAN program, such as MODFLOW."""
from __future__ import print_function

__author__ = "Christian D. Langevin"
__date__ = "October 26, 2014"
__version__ = "1.1.0"
__maintainer__ = "Christian D. Langevin"
__email__ = "langevin@usgs.gov"
__status__ = "Production"
__description__ = '''
This is the pymake program for compiling fortran source files, such as
the source files that come with MODFLOW. The program works by building
a directed acyclic graph of the module dependencies and then compiling
the source files in the proper order.
'''

import os
import sys
import traceback
import shutil
from subprocess import Popen, PIPE, STDOUT
import argparse
import datetime

from .dag import order_source_files, order_c_source_files

try:
    from flopy import is_exe as flopy_is_exe

    flopy_avail = True
except:
    flopy_avail = False

PY3 = sys.version_info[0] >= 3

# define temporary directories
srcdir_temp = os.path.join('.', 'src_temp')
objdir_temp = os.path.join('.', 'obj_temp')
moddir_temp = os.path.join('.', 'mod_temp')


def parser():
    """Construct the parser and return argument values."""
    description = __description__
    parser = argparse.ArgumentParser(description=description,
                                     epilog='''Note that the source directory
                                     should not contain any bad or duplicate
                                     source files as all source files in the
                                     source directory will be built and
                                     linked.''')
    parser.add_argument('srcdir', help='Location of source directory')
    parser.add_argument('target', help='Name of target to create')
    parser.add_argument('-fc',
                        help='Fortran compiler to use (default is gfortran)',
                        default='gfortran', choices=['ifort', 'mpiifort',
                                                     'gfortran'])
    parser.add_argument('-cc', help='C compiler to use (default is gcc)',
                        default='gcc', choices=['gcc', 'clang', 'icc',
                                                'mpiicc', 'g++', 'cl'])
    parser.add_argument('-ar', '--arch',
                        help='Architecture to use for ifort (default is intel64)',
                        default='intel64',
                        choices=['ia32', 'ia32_intel64', 'intel64'])
    parser.add_argument('-mc', '--makeclean', help='Clean files when done',
                        action='store_true')
    parser.add_argument('-dbl', '--double', help='Force double precision',
                        action='store_true')
    parser.add_argument('-dbg', '--debug', help='Create debug version',
                        action='store_true')
    parser.add_argument('-e', '--expedite',
                        help='''Only compile out of date source files.
                        Clean must not have been used on previous build.
                        Does not work yet for ifort.''',
                        action='store_true')
    parser.add_argument('-dr', '--dryrun',
                        help='''Do not actually compile.  Files will be
                        deleted, if --makeclean is used.
                        Does not work yet for ifort.''',
                        action='store_true')
    parser.add_argument('-sd', '--subdirs',
                        help='''Include source files in srcdir
                        subdirectories.''',
                        action='store_true')
    parser.add_argument('-ff', '--fflags',
                        help='''Additional fortran compiler flags.''',
                        default=None)
    parser.add_argument('-cf', '--cflags',
                        help='''Additional c compiler flags.''',
                        default=None)
    parser.add_argument('-sl', '--syslibs',
                        help='''Linker system libraries.''',
                        default='-lc',
                        choices=['-lc', '-lm'])
    parser.add_argument('-mf', '--makefile',
                        help='''Create a standard makefile.''',
                        action='store_true')
    parser.add_argument('-cm', '--cmake',
                        help='''File with DAG sorted source files for CMAKE.''',
                        default=None)
    parser.add_argument('-cs', '--commonsrc',
                        help='''Additional directory with common source files.''',
                        default=None)
    parser.add_argument('-ef', '--extrafiles',
                        help='''List of extra source files to include in the
                        compilation.  extrafiles can be either a list of files
                        or the name of a text file that contains a list of
                        files.''',
                        default=None)
    parser.add_argument('-exf', '--excludefiles',
                        help='''List of extra source files to exclude from the
                        compilation.  excludefiles can be either a list of 
                        files or the name of a text file that contains a list
                        of files.''',
                        default=None)
    parser.add_argument('-so', '--sharedobject', help='Create shared object',
                        action='store_false')
    args = parser.parse_args()
    return args


def process_Popen_stdout(proc):
    """
    Generic function to write Popen stdout data to the terminal.

    Parameters
    ----------
    proc : Popen
        Popen instance

    Returns
    -------
    """
    # write stdout to the terminal
    while True:
        line = proc.stdout.readline()
        c = line.decode('utf-8')
        if c != '':
            c = c.rstrip('\r\n')
            print('{}'.format(c))
        else:
            break

    # setup a communicator so that the Popen return code is set
    proc.communicate()

    return


def process_Popen_command(shellflg, cmdlist):
    """
    Generic function to write Popen command data to the screen.

    Parameters
    ----------
    shellflg : bool
        boolean indicating if output is sent to shell by Popen

    cmdlist : list
        command list passed to Popen

    Returns
    -------
    """
    if not shellflg:
        if isinstance(cmdlist, str):
            print(cmdlist)
        elif isinstance(cmdlist, list):
            print(' '.join(cmdlist))
    return


def process_Popen_communicate(proc):
    """
    Generic function to write communication information from Popen to the
    screen.

    Parameters
    ----------
    proc : Popen
        Popen instance

    Returns
    -------
    returncode : int
        proc.returncode

    """
    stdout, stderr = proc.communicate()

    if stdout:
        if PY3:
            stdout = stdout.decode()
        print(stdout)
    if stderr:
        if PY3:
            stderr = stderr.decode()
        print(stderr)

    # catch non-zero return code
    if proc.returncode != 0:
        msg = '{} failed\n'.format(' '.join(proc.args)) + \
              '\tstatus code {}\n'.format(proc.returncode)
        print(msg)

    return


def initialize(srcdir, target, commonsrc, extrafiles, excludefiles):
    """
    Remove temp source directory and target, and then copy source into
    source temp directory.

    Return temp directory path.
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
    files = parse_extrafiles(extrafiles)
    if files is None:
        files = []
    for fname in files:
        if not os.path.isfile(fname):
            print('Current working directory: {}'.format(os.getcwd()))
            print('Error in extrafiles: {}'.format(extrafiles))
            print('Could not find file: {}'.format(fname))
            raise Exception()
        dst = os.path.join(srcdir_temp, os.path.basename(fname))
        if os.path.isfile(dst):
            raise Exception('Error with extrafile.  Name conflicts with '
                            'an existing source file: {}'.format(dst))
        shutil.copy(fname, dst)

    # if exclude is not None, then it is a text file with a list of
    # source files that need to be excluded from srctemp.
    files = parse_extrafiles(excludefiles)
    if files is None:
        files = []
    for fname in files:
        if not os.path.isfile(fname):
            print('Current working directory: {}'.format(os.getcwd()))
            print('Warning in excludefiles: {}'.format(excludefiles))
            print('Could not find file: {}'.format(fname))
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


def parse_extrafiles(extrafiles):
    if extrafiles is None:
        files = None
    else:
        if isinstance(extrafiles, list):
            files = extrafiles
        elif os.path.isfile(extrafiles):
            efpth = os.path.dirname(extrafiles)
            with open(extrafiles, 'r') as f:
                files = []
                for line in f:
                    fname = line.strip().replace('\\', '/')
                    if len(fname) > 0:
                        fname = os.path.abspath(os.path.join(efpth, fname))
                        files.append(fname)
        else:
            raise Exception('extrafiles must be either a list of files '
                            'or the name of a text file that contains a list'
                            'of files.')
    return files


def clean(objext, intelwin):
    """
    Remove mod and object files, and remove the temp source directory.

    """
    # clean things up
    print('\nCleaning up temporary source, object, and module files...')
    filelist = os.listdir('.')
    delext = ['.mod', objext]
    for f in filelist:
        for ext in delext:
            if f.endswith(ext):
                os.remove(f)

    # remove temporary directories
    shutil.rmtree(srcdir_temp)
    shutil.rmtree(objdir_temp)
    shutil.rmtree(moddir_temp)
    if intelwin:
        os.remove('compile.bat')
    return


def get_ordered_srcfiles(srcdir, include_subdir=False):
    """
    Create a list of ordered source files (both fortran and c).

    Ordering is build using a directed acyclic graph to determine module
    dependencies.
    """
    # create a list of all c(pp), f and f90 source files

    templist = []
    for path, subdirs, files in os.walk(srcdir):
        for name in files:
            if not include_subdir:
                if path != srcdir:
                    continue
            f = os.path.join(os.path.join(path, name))
            templist.append(f)
    cfiles = []  # mja
    srcfiles = []
    for f in templist:
        if f.lower().endswith('.f') or f.lower().endswith('.f90') \
                or f.lower().endswith('.for') or f.lower().endswith('.fpp'):
            srcfiles.append(f)
        elif f.lower().endswith('.c') or f.lower().endswith('.cpp'):  # mja
            cfiles.append(f)  # mja

    # orderedsourcefiles = order_source_files(srcfiles) + \
    #                     order_c_source_files(cfiles)

    srcfileswithpath = []
    for srcfile in srcfiles:
        s = os.path.join(srcdir, srcfile)
        s = srcfile
        srcfileswithpath.append(s)

    # from mja
    cfileswithpath = []
    for srcfile in cfiles:
        s = os.path.join(srcdir, srcfile)
        s = srcfile
        cfileswithpath.append(s)

    # order the source files using the directed acyclic graph in dag.py
    orderedsourcefiles = []
    if len(srcfileswithpath) > 0:
        orderedsourcefiles += order_source_files(srcfileswithpath)

    if len(cfileswithpath) > 0:
        orderedsourcefiles += order_c_source_files(cfileswithpath)

    return orderedsourcefiles


def create_openspec():
    """
    Create new openspec.inc, FILESPEC.INC, and filespec.inc files that uses
    STREAM ACCESS.

    This is specific to MODFLOW and MT3D based targets.
    """
    files = ['openspec.inc', 'filespec.inc']
    dirs = [d[0] for d in os.walk(srcdir_temp)]
    for d in dirs:
        for file in files:
            fpth = os.path.join(d, file)
            if os.path.isfile(fpth):
                print('replacing..."{}"'.format(fpth))
                f = open(fpth, 'w')
                line = "c -- created by pymake.py\n" + \
                       "      CHARACTER*20 ACCESS,FORM,ACTION(2)\n" + \
                       "      DATA ACCESS/'STREAM'/\n" + \
                       "      DATA FORM/'UNFORMATTED'/\n" + \
                       "      DATA (ACTION(I),I=1,2)/'READ','READWRITE'/\n" + \
                       "c -- end of include file\n"
                f.write(line)
                f.close()
    return


def out_of_date(srcfile, objfile):
    ood = True
    if os.path.exists(objfile):
        t1 = os.path.getmtime(objfile)
        t2 = os.path.getmtime(srcfile)
        if t1 > t2:
            ood = False
    return ood


# determine if iso_c_binding is used so that correct
# gcc and clang compiler flags can be set
def get_iso_c(srcfiles):
    for srcfile in srcfiles:
        try:
            f = open(srcfile, 'rb')
        except:
            print('get_f_nodelist: could not open {0}'.format(
                os.path.basename(srcfile)))
            continue
        lines = f.read()
        lines = lines.decode('ascii', 'replace').splitlines()

        # develop a list of modules in the file
        for idx, line in enumerate(lines):
            linelist = line.strip().split()
            if len(linelist) == 0:
                continue
            if linelist[0].upper() == 'USE':
                modulename = linelist[1].split(',')[0].upper()
                if 'ISO_C_BINDING' == modulename:
                    return True
    return False


def flag_available(flag):
    """
    Determine if a specified flag exists.

    Not all flags will be detected, for example -O2 -fbounds-check=on
    """

    # set shell flag based on os
    shellflg = False
    if sys.platform == 'win32':
        shellflg = True

    # determine the gfortran command line flags available
    cmdlist = ['gfortran', '--help', '-v']
    proc = Popen(cmdlist, stdout=PIPE, stderr=PIPE, shell=shellflg)
    process_Popen_command(shellflg, cmdlist)

    # establish communicator
    stdout, stderr = proc.communicate()

    if PY3:
        stdout = stdout.decode()

    avail = flag in stdout
    msg = '  {} flag available: {}'.format(flag, avail)
    print(msg)

    return avail


def get_osname():
    """
    Return the lower case OS platform name.

    Parameters
    -------

    Returns
    -------
    str : str
        lower case OS platform name
    """
    return sys.platform.lower()


def get_prepend(compiler, osname):
    """
    Return the appropriate prepend for a compiler switch for a OS.

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


def fortran_files(srcfiles, extensions=False):
    """
    Return a list of fortran files or unique fortran file extensions.

    Parameters
    -------
    srcfiles : list
        list of sourcefile names
    extensions : bool
        flag controls return of either a list of fortran files or
        a list of unique fortran file extensions

    Returns
    -------
    list : list
        list of fortran files or unique fortran file extensions
    """
    l = []
    for srcfile in srcfiles:
        ext = os.path.splitext(srcfile)[1]
        if ext.lower() in ['.f', '.for', '.f90', '.fpp']:
            if extensions:
                # save unique extension
                if ext not in l:
                    l.append(ext)
            else:
                l.append(srcfile)
    if len(l) < 1:
        l = None
    return l


def c_files(srcfiles, extensions=False):
    """
    Return a list of c and cpp files or unique c and cpp file extensions.

    Parameters
    -------
    srcfiles : list
        list of sourcefile names
    extensions : bool
        flag controls return of either a list of c and cpp files or
        a list of unique c and cpp file extensions

    Returns
    -------
    list : list
        list of c or cpp files or uniques c and cpp file extensions
    """
    l = []
    for srcfile in srcfiles:
        ext = os.path.splitext(srcfile)[1]
        if ext.lower() in ['.c', '.cpp']:
            if extensions:
                if ext not in l:
                    l.append(ext)
            else:
                l.append(srcfile)
    if len(l) < 1:
        l = None
    return l


def get_optlevel(fc, cc, debug, fflags, cflags, osname=None):
    """
    Return a compiler optimization switch.

    Parameters
    -------
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
    # get lower case OS string
    if osname is None:
        osname = get_osname()

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

    # prepend optlevel
    optlevel = prepend + optlevel

    return optlevel


def get_fortran_flags(fc, fflags, debug, double, sharedobject=False,
                      osname=None):
    """
    Return a list of standard pymake and user specified fortran compiler
    switches.

    Parameters
    -------
    fc : str
        fortran compiler
    fflags : list
        user provided list of fortran compiler flags
    debug : bool
        flag indicating a debug executable will be built
    double : bool
        flag indicating a double precision executable will be built
    sharedobject : bool
        flag indicating a shared object (.so or .dll) will be built
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

        # get lower case OS string
        if osname is None:
            osname = get_osname()

        # get - or / to prepend for compiler switches
        prepend = get_prepend(fc, osname)

        # generate standard fortran flags
        if fc == 'gfortran':
            if sharedobject:
                flags.append('fPIC')
            flags.append('fbacktrace')
            if osname == 'win32':
                flags.append('Bstatic')
            if debug:
                flags += ['g', 'fcheck=all', 'fbounds-check', 'Wall']
                if flag_available('-ffpe-trap'):
                    flags.append('ffpe-trap=overflow,zero,invalid,denormal')
            else:
                if flag_available('-ffpe-summary'):
                    flags.append('ffpe-summary=overflow')
                if flag_available('-ffpe-trap'):
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

        # add prepend to compiler flags
        for idx, flag in enumerate(flags):
            flags[idx] = prepend + flag

    return flags


def get_c_flags(cc, cflags, debug, double, srcfiles, sharedobject=False,
                osname=None):
    """
    Return a list of standard pymake and user specified c or cpp compiler
    switches.

    Parameters
    -------
    cc : str
        c or cpp compiler
    cflags : list
        user provided list of c or cpp compiler flags
    debug : bool
        flag indicating a debug executable will be built
    double : bool
        flag indicating a double precision executable will be built
    srcfiles : list
        list of sourcefile names
    sharedobject : bool
        flag indicating a shared object (.so or .dll) will be built
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

        # get lower case OS string
        if osname is None:
            osname = get_osname()

        # get - or / to prepend for compiler switches
        prepend = get_prepend(cc, osname)

        # generate c flags
        if cc in ['gcc', 'g++', 'clang']:
            if sharedobject:
                flags.append('fPIC')
            if osname == 'win32':
                flags.append('Bstatic')
            if debug:
                flags += ['g']
                if flag_available('-Wall'):
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
        ffiles = fortran_files(srcfiles)
        cfiles = c_files(srcfiles)
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

        # add prepend to compiler flags
        for idx, flag in enumerate(flags):
            flags[idx] = prepend + flag

    return flags


def get_linker_flags(fc, cc, fflags, cflags, debug, double, srcfiles,
                     syslibs, sharedobject=False, osname=None):
    """
    Return a list of standard pymake and user specified c or cpp compiler
    switches.

    Parameters
    -------
    cc : str
        c or cpp compiler
    cflags : list
        user provided list of c or cpp compiler flags
    debug : bool
        flag indicating a debug executable will be built
    double : bool
        flag indicating a double precision executable will be built
    srcfiles : list
        list of sourcefile names
    sharedobject : bool
        flag indicating a shared object (.so or .dll) will be built
    osname : str
        optional lower case OS name. If not passed it will be determined
        using sys.platform

    Returns
    -------
    flags : str
        c or cpp compiler switches
    """
    compiler = fc
    if compiler is None:
        compiler = cc

    # remove .exe extension of necessary
    if '.exe' in compiler.lower():
        compiler = compiler[:-4]

    # get lower case OS string
    if osname is None:
        osname = get_osname()

    # get - or / to prepend for compiler switches
    prepend = get_prepend(compiler, osname)

    if compiler in ['gfortran', 'ifort', 'mpiifort']:
        flags = get_fortran_flags(compiler, fflags, debug, double,
                                  sharedobject=sharedobject, osname=osname)
    elif compiler in ['gcc', 'g++', 'clang', 'clang++',
                      'icc', 'icpc', 'icl', 'cl',
                      'mpiicc', 'mpiicpc']:
        flags = get_c_flags(compiler, cflags, debug, double, srcfiles,
                            sharedobject=sharedobject, osname=osname)

    if sharedobject:
        tag = prepend + 'fPIC'
        ipos = flags.index(tag)
        if osname == 'darwin':
            copt = prepend + 'dynamiclib'
        else:
            copt = prepend + 'shared'
        flags.insert(ipos, copt)

    # set outgoing syslibs
    syslibs_out = []

    # add passed syslibs flags - assume that flags have - or / as the
    # first character.
    for flag in syslibs:
        if flag[1:] not in syslibs_out:
            syslibs_out.append(flag[1:])

    # add prepend to syslibs flags
    for idx, flag in enumerate(syslibs_out):
        syslibs_out[idx] = prepend + flag

    return compiler, flags, syslibs_out


def compile(srcfiles, target, fc, cc,
            expedite, dryrun, double, debug,
            fflags, cflags, syslibs, arch, intelwin,
            sharedobject):
    """
    Standard compile method

    """
    # initialize returncode
    returncode = 0

    # initialize ilink
    ilink = 0

    # set optimization levels
    optlevel = get_optlevel(fc, cc, debug, fflags, cflags)

    # get fortran and c compiler switches
    tfflags = get_fortran_flags(fc, fflags, debug, double,
                                sharedobject=sharedobject)
    tcflags = get_c_flags(cc, cflags, debug, double, srcfiles,
                          sharedobject=sharedobject)

    # get linker flags and syslibs
    lc, tlflags, tsyslibs = get_linker_flags(fc, cc, fflags, cflags,
                                             debug, double,
                                             srcfiles, syslibs,
                                             sharedobject=sharedobject)

    # clean exe prior to build so that test for exe below can return a
    # non-zero error code
    if flopy_avail:
        if flopy_is_exe(target):
            os.remove(target)

    if intelwin:
        # update compiler names if necessary
        ext = '.exe'
        if fc is not None:
            if ext not in fc:
                fc += ext
        if cc is not None:
            if ext not in cc:
                cc += ext
        if ext not in lc:
            lc += ext
        if ext not in target:
            target += ext

        # update target extension if shared object
        if sharedobject:
            ttarget, ext = os.path.splitext(target)
            if ext.lower() != '.dll':
                target = ttarget + '.dll'

        # delete the batch file if it exists
        batchfile = 'compile.bat'
        if os.path.isfile(batchfile):
            try:
                os.remove(batchfile)
            except:
                print("could not remove '{}'".format(batchfile))

        # Create target using a batch file on Windows
        try:
            create_win_batch(batchfile, fc, cc, lc, optlevel,
                             tfflags, tcflags, tlflags, tsyslibs,
                             srcfiles, target, arch)

            # build the command list for the Windows batch file
            cmdlists = [batchfile, ]
        except:
            errmsg = 'Could not make x64 target: {}\n'.format(target)
            errmsg += traceback.print_exc()
            print(errmsg)

    else:
        if sharedobject:
            ext = os.path.splitext(target)[-1].lower()
            if ext != '.so':
                target += '.so'

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
            if ext in ['.c', '.cpp']:  # mja
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
                    cmdlist.append('-I{}'.format(sd))
            # put object files and module files in objdir_temp and moddir_temp
            else:
                cmdlist.append('-I{}'.format(objdir_temp))
                if fc in ['ifort', 'mpiifort']:
                    cmdlist.append('-module')
                    cmdlist.append(moddir_temp + '/')
                else:
                    cmdlist.append('-J{}'.format(moddir_temp))

            cmdlist.append('-c')
            cmdlist.append(srcfile)

            # object file name and location
            srcname, srcext = os.path.splitext(srcfile)
            srcname = srcname.split(os.path.sep)[-1]
            objfile = os.path.join(objdir_temp, srcname + '.o')
            cmdlist.append('-o')
            cmdlist.append(objfile)

            # Save the name of the object file for linker
            objfiles.append(objfile)

            # If expedited, then check if object file is out of date, if it
            # exists. No need to compile if object file is newer.
            compilefile = True
            if expedite:
                if not out_of_date(srcfile, objfile):
                    compilefile = False

            if compilefile:
                cmdlists.append(cmdlist)

        # Build the link command and then link to create the executable
        ilink = len(cmdlists)
        if ilink > 0:
            cmdlist = [lc, optlevel]
            for switch in tlflags:
                cmdlist.append(switch)

            cmdlist.append('-o')
            cmdlist.append(target)
            for objfile in objfiles:
                cmdlist.append(objfile)

            for switch in tsyslibs:
                cmdlist.append(switch)

            # add linker
            cmdlists.append(cmdlist)

    # execute each command in cmdlists
    if not dryrun:
        for idx, cmdlist in enumerate(cmdlists):
            if idx == 0:
                if intelwin:
                    msg = "\nCompiling '{}' ".format(os.path.basename(target)) + \
                          'for Windows using Intel compilers...'
                else:
                    msg = "\nCompiling object files for " + \
                          "'{}'...".format(os.path.basename(target))
                print(msg)
            if idx > 0 and idx == ilink:
                msg = "\nLinking object files " + \
                      "to make '{}'...".format(os.path.basename(target))
                print(msg)

            # write the command to the terminal
            process_Popen_command(False, cmdlist)

            # run the command using Popen
            proc = Popen(cmdlist, shell=False, stdout=PIPE, stderr=PIPE)

            # write batch file execution to terminal
            if intelwin:
                process_Popen_stdout(proc)
            # establish communicator to report errors
            else:
                process_Popen_communicate(proc)

            # set return code
            returncode = proc.returncode

    # return
    return returncode


def create_win_batch(batchfile, fc, cc, lc, optlevel,
                     fflags, cflags, lflags, syslibs,
                     srcfiles, target, arch):
    """
    Make an intel compiler batch file for compiling on windows.

    """
    # get path to compilervars batch file
    iflist = ['IFORT_COMPILER{}'.format(i) for i in range(30, 12, -1)]
    found = False
    for ift in iflist:
        cpvars = os.environ.get(ift)
        if cpvars is not None:
            found = True
            break
    if not found:
        raise Exception('Pymake could not find IFORT compiler.')
    cpvars += os.path.join('bin', 'compilervars.bat')
    if not os.path.isfile(cpvars):
        raise Exception('Could not find cpvars: {}'.format(cpvars))
    f = open(batchfile, 'w')
    line = 'call ' + '"' + os.path.normpath(cpvars) + '" ' + arch + '\n'
    f.write(line)

    # assume that header files may be in other folders, so make a list
    searchdir = []
    for s in srcfiles:
        dirname = os.path.dirname(s)
        if dirname not in searchdir:
            searchdir.append(dirname)

    # write commands to build object files
    for srcfile in srcfiles:
        if srcfile.endswith('.c') or srcfile.endswith('.cpp'):
            cmd = cc + ' ' + optlevel + ' '
            for switch in cflags:
                cmd += switch + ' '
            cmd += '/c' + ' '

            # add search path for any header files
            for sd in searchdir:
                cmd += '/I{} '.format(sd)

            obj = os.path.join(objdir_temp,
                               os.path.splitext(os.path.basename(srcfile))[0]
                               + '.obj')
            cmd += '/Fo:' + obj + ' '
            cmd += srcfile
        else:
            cmd = fc + ' ' + optlevel + ' '
            for switch in fflags:
                cmd += switch + ' '
            cmd += '/c' + ' '
            cmd += '/module:{0}\\ '.format(moddir_temp)
            cmd += '/object:{0}\\ '.format(objdir_temp)
            cmd += srcfile
        f.write("echo compiling '" + os.path.basename(srcfile) + "'\n")
        f.write(cmd + '\n')

    # write commands to link
    line = "echo Linking oject files to create '" + \
           os.path.basename(target) + "'\n"
    f.write(line)

    # assemble the link command
    cmd = lc + ' ' + optlevel
    for switch in lflags:
        cmd += ' ' + switch
    cmd += ' ' + '-o' + ' ' + target + ' ' + objdir_temp + '\\*.obj'
    for switch in syslibs:
        cmd += ' ' + switch
    cmd += '\n'
    f.write(cmd)

    # close the batch file
    f.close()

    return


def create_makefile(target, srcdir, srcdir2, extrafiles,
                    srcfiles, debug, double,
                    fc, cc, fflags, cflags, syslibs,
                    objext='.o',
                    makedefaults='makedefaults'):
    # get list of unique fortran and c/c++ file extensions
    fext = fortran_files(srcfiles, extensions=True)
    cext = c_files(srcfiles, extensions=True)

    # build heading
    heading = '# makefile created on {}\n'.format(datetime.datetime.now()) + \
              '# by pymake (version {})\n'.format(__version__)
    heading += '# using the'
    if fext is not None:
        heading += " '{}' fortran".format(fc)
        if cext is not None:
            heading += ' and'
    if cext is not None:
        heading += " '{}' c/c++".format(cc)
    heading += ' compiler(s).\n'

    # open makefile
    f = open('makefile', 'w')

    # write header
    f.write(heading + '\n')

    #  write include file
    line = '\ninclude ./{}\n\n'.format(makedefaults)
    f.write(line)

    # determine the directories with source files
    # source files in sdir and sdir2
    dirs = [d[0].replace('\\', '/') for d in os.walk(srcdir)]
    if srcdir2 is not None:
        dirs2 = [d[0].replace('\\', '/') for d in os.walk(srcdir2)]
        dirs = dirs + dirs2

    # source files in extrafiles
    files = parse_extrafiles(extrafiles)
    if files is not None:
        for ef in files:
            fdir = os.path.dirname(ef)
            rdir = os.path.relpath(fdir, os.getcwd())
            rdir = rdir.replace('\\', '/')
            if rdir not in dirs:
                dirs.append(rdir)

    # write directories with source files and create vpath data
    line = '# Define the source file directories\n'
    f.write(line)
    vpaths = []
    for idx, dir in enumerate(dirs):
        vpaths.append('SOURCEDIR{}'.format(idx + 1))
        line = '{}={}\n'.format(vpaths[idx], dir)
        f.write(line)
    f.write('\n')

    # write vpath
    f.write('VPATH = \\\n')
    for idx, sd in enumerate(vpaths):
        f.write('${' + '{}'.format(sd) + '} ')
        if idx + 1 < len(vpaths):
            f.write('\\')
        f.write('\n')
    f.write('\n')

    # write file extensions
    line = '.SUFFIXES: '
    if fext is not None:
        for ext in fext:
            line += '{} '.format(ext)
    if cext is not None:
        for ext in cext:
            line += '{} '.format(ext)
    line += objext
    f.write('{}\n'.format(line))
    f.write('\n')

    f.write('OBJECTS = \\\n')
    for idx, srcfile in enumerate(srcfiles):
        objpth = os.path.splitext(os.path.basename(srcfile))[0] + objext
        f.write('$(OBJDIR)/{} '.format(objpth))
        if idx + 1 < len(srcfiles):
            f.write('\\')
        f.write('\n')
    f.write('\n')

    f.write('# Define the objects that make up the program\n')
    f.write('$(PROGRAM) : $(OBJECTS)\n')
    if fc is None:
        line = '\t-$(CC) $(OPTLEVEL) $(CFLAGS) -o $@ $(OBJECTS)\n'
    else:
        line = '\t-$(FC) $(OPTLEVEL) $(FFLAGS) -o $@ $(OBJECTS) $(SYSLIBS)\n'
    f.write('{}\n'.format(line))

    if fext is not None:
        for ext in fext:
            f.write('$(OBJDIR)/%{} : %{}\n'.format(objext, ext))
            f.write('\t@mkdir -p $(@D)\n')
            line = '\t$(FC) $(OPTLEVEL) $(FFLAGS) -c $< -o $@ ' + \
                   '$(INCSWITCH) $(MODSWITCH)\n'
            f.write('{}\n'.format(line))

    if cext is not None:
        for ext in cext:
            f.write('$(OBJDIR)/%{} : %{}\n'.format(objext, ext))
            f.write('\t@mkdir -p $(@D)\n')
            line = '\t$(CC) $(OPTLEVEL) $(CFLAGS) -c $< -o $@ ' + \
                   '$(INCSWITCH)\n'
            f.write('{}\n'.format(line))

    # close the makefile
    f.close()

    # open makedefaults
    f = open(makedefaults, 'w')

    # replace makefile in heading with makedefaults
    heading = heading.replace('makefile', makedefaults)

    # write header
    f.write(heading + '\n')

    # write OS evaluation
    line = '# determine OS\n'
    line += 'ifeq ($(OS), Windows_NT)\n'
    line += '\tdetected_OS = Windows\n'
    line += '\tOS_macro = -D_WIN32\n'
    line += 'else\n'
    line += "\tdetected_OS = $(shell sh -c 'uname 2>/dev/null " + \
            "|| echo Unknown')\n"
    line += '\tifeq ($(detected_OS), Darwin)\n'
    line += '\t\tOS_macro = -D__APPLE__\n'
    line += '\telse\n'
    line += '\t\tOS_macro = -D__LINUX__\n'
    line += '\tendif\n'
    line += 'endif\n\n'
    f.write(line)

    # get path to executable
    dpth = os.path.dirname(target)
    if len(dpth) > 0:
        dpth = os.path.relpath(dpth)
    else:
        dpth = '.'

    # write
    line = '# Define the directories for the object and module files\n' + \
           '# and the executable and its path.\n'
    line += 'BINDIR = {}\n'.format(dpth)
    line += 'OBJDIR = {}\n'.format(objdir_temp)
    line += 'MODDIR = {}\n'.format(moddir_temp)
    line += 'INCSWITCH = -I $(OBJDIR)\n'
    line += 'MODSWITCH = -J $(MODDIR)\n\n'
    f.write(line)

    exe_name = os.path.splitext(os.path.basename(target))[0]
    line = '# define os dependent executable name\n'
    line += 'ifeq ($(detected_OS), Windows)\n'
    line += '\tPROGRAM = {}.exe\n'.format(exe_name)
    line += 'else\n'
    line += '\tPROGRAM = {}\n'.format(exe_name)
    line += 'endif\n\n'
    f.write(line)

    # set gfortran as compiler if it is f77
    line = '# set fortran compiler to gfortran if it is f77\n'
    line += 'ifeq ($(FC), f77)\n'
    line += '\tFC = gfortran\n'
    line += '\t# set c compiler to gcc if not passed on the command line\n'
    line += '\tifneq ($(origin CC), "command line")\n'
    line += '\t\tifneq ($(CC), gcc)\n'
    line += '\t\t\tCC = gcc\n'
    line += '\t\tendif\n'
    line += '\tendif\n'
    line += 'endif\n\n'
    f.write(line)

    # optimization level
    optlevel = get_optlevel(fc, cc, debug, fflags, cflags)
    line = '# set the optimization level (OPTLEVEL) if not defined\n'
    line += 'OPTLEVEL ?= {}\n\n'.format(optlevel)
    f.write(line)

    # fortran flags
    if fext is not None:
        line = '# set the fortran flags\n'
        line += 'ifeq ($(detected_OS), Windows)\n'
        line += '\tifeq ($(FC), gfortran)\n'
        tfflags = get_fortran_flags('gfortran', fflags, debug, double,
                                    osname='win32')
        line += '\t\tFFLAGS ?= {}\n'.format(' '.join(tfflags))
        line += '\tendif\n'
        line += 'else\n'
        line += '\tifeq ($(FC), gfortran)\n'
        tfflags = get_fortran_flags('gfortran', fflags, debug, double,
                                    osname='linux')
        for idx, flag in enumerate(tfflags):
            if '-D__' in flag:
                tfflags[idx] = '$(OS_macro)'
        line += '\t\tFFLAGS ?= {}\n'.format(' '.join(tfflags))
        line += '\tendif\n'
        line += '\tifeq ($(FC), ifort mpiifort)\n'
        tfflags = get_fortran_flags('ifort', fflags, debug, double,
                                    osname='linux')
        line += '\t\tFFLAGS ?= {}\n'.format(' '.join(tfflags))
        line += '\t\tMODSWITCH = -module $(MODDIR)\n'
        line += '\tendif\n'
        line += 'endif\n\n'
        f.write(line)

    # c/c++ flags
    if cext is not None:
        line = '# set the c/c++ flags\n'
        line += 'ifeq ($(detected_OS), Windows)\n'
        line += '\tifeq ($(FC), gcc g++ clang clang++)\n'
        tcflags = get_c_flags('gcc', fflags, debug, double, srcfiles,
                              osname='win32')
        line += '\t\tCFLAGS ?= {}\n'.format(' '.join(tcflags))
        line += '\tendif\n'
        line += 'else\n'
        line += '\tifeq ($(FC), gcc g++ clang clang++)\n'
        tcflags = get_c_flags('gcc', fflags, debug, double, srcfiles,
                              osname='linux')
        line += '\t\tCFLAGS ?= {}\n'.format(' '.join(tcflags))
        line += '\tendif\n'
        line += '\tifeq ($(FC), icc mpiicc icpc)\n'
        tcflags = get_c_flags('icc', fflags, debug, double, srcfiles,
                              osname='linux')
        line += '\t\tCFLAGS ?= {}\n'.format(' '.join(tcflags))
        line += '\tendif\n'
        line += 'endif\n\n'
        f.write(line)

    # syslibs
    line = '# set the syslibs\n'
    line += 'ifeq ($(detected_OS), Windows)\n'
    _, tlink_flags, tsyslibs = get_linker_flags('gfortran', 'gcc',
                                                fflags, cflags,
                                                debug, double,
                                                srcfiles, syslibs,
                                                osname='win32')
    line += '\tSYSLIBS ?= {}\n'.format(' '.join(tsyslibs))
    line += 'else\n'
    if fc is None:
        line += '\tifeq ($(CC), gcc g++ clang clang++)\n'
    else:
        line += '\tifeq ($(FC), gfortran)\n'
    _, tlink_flags, tsyslibs = get_linker_flags('gfortran', 'gcc',
                                                fflags, cflags,
                                                debug, double,
                                                srcfiles, syslibs,
                                                osname='linux')
    line += '\t\tSYSLIBS ?= {}\n'.format(' '.join(tsyslibs))
    line += '\tendif\n'
    if fc is None:
        line += '\tifeq ($(CC), icc icpc mpiicc)\n'
    else:
        line += '\tifeq ($(FC), ifort mpiifort)\n'
    _, tlink_flags, tsyslibs = get_linker_flags('ifort', 'icc',
                                                fflags, cflags,
                                                debug, double,
                                                srcfiles, syslibs,
                                                osname='linux')
    line += '\t\tSYSLIBS ?= {}\n'.format(' '.join(tsyslibs))
    line += '\tendif\n'
    line += 'endif\n\n'
    f.write(line)

    # task functions
    line = '# Define task functions\n'
    line += '# Create the bin directory and compile and link the program\n'
    line += 'all: makedirs | $(PROGRAM)\n\n'
    line += '# Make the bin directory for the executable\n'
    line += 'makedirs:\n'
    line += '\tmkdir -p $(BINDIR)\n'
    line += '\tmkdir -p $(MODDIR)\n\n'
    line += '# Write selected compiler settings\n'
    line += '.PHONY: settings\n'
    line += 'settings:\n'
    line += '\t@echo "Optimization level: $(OPTLEVEL)"\n'
    if fext is not None:
        line += '\t@echo "Fortran compiler:   $(FC)"\n'
        line += '\t@echo "Fortran flags:      $(FFLAGS)"\n'
    if cext is not None:
        line += '\t@echo "C compiler:         $(CC)"\n'
        line += '\t@echo "C flags:            $(CFLAGS)"\n'
    line += '\t@echo "SYSLIBS:            $(SYSLIBS)"\n\n'
    line += '# Clean the object and module files and the executable\n'
    line += '.PHONY: clean\n'
    line += 'clean:\n'
    line += '\t-rm -rf $(OBJDIR)\n'
    line += '\t-rm -rf $(MODDIR)\n'
    line += '\t-rm -rf $(PROGRAM)\n\n'
    line += '# Clean the object and module files\n'
    line += '.PHONY: cleanobj\n'
    line += 'cleanobj:\n'
    line += '\t-rm -rf $(OBJDIR)\n'
    line += '\t-rm -rf $(MODDIR)\n\n'
    f.write(line)

    # close the makedefaults
    f.close()

    return


def main(srcdir, target, fc='gfortran', cc='gcc', makeclean=True,
         expedite=False, dryrun=False, double=False, debug=False,
         include_subdirs=False, fflags=None, cflags=None, syslibs=None,
         arch='intel64', makefile=False, srcdir2=None, extrafiles=None,
         excludefiles=None, cmake=None, sharedobject=False):
    """Main part of program."""
    # initialize return code
    returncode = 0

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
    print('\nsource files are in:\n    {}\n'.format(srcdir))
    print('executable name to be created:\n    {}\n'.format(target))
    if srcdir2 is not None:
        print('additional source files are in:\n     {}\n'.format(srcdir2))

    # make sure the path for the target exists
    pth = os.path.dirname(target)
    if pth == '':
        pth = '.'
    if not os.path.exists(pth):
        print('creating target path - {}\n'.format(pth))
        os.makedirs(pth)

    # initialize
    initialize(srcdir, target, srcdir2, extrafiles, excludefiles)

    if cmake is not None:
        if excludefiles is not None:
            efiles = [os.path.basename(fpth) for fpth in
                      parse_extrafiles(excludefiles)]
        else:
            efiles = []
        csrcfiles = get_ordered_srcfiles(srcdir, include_subdirs)
        f = open(cmake, 'w')
        fstart = os.path.dirname(cmake)
        for fpth in csrcfiles:
            fname = os.path.basename(fpth)
            if fname not in efiles:
                fpthr = os.path.relpath(fpth, fstart)
                f.write('{}\n'.format(os.path.join(fpthr)))
        f.close()

    # get ordered list of files to compile
    srcfiles = get_ordered_srcfiles(srcdir_temp, include_subdirs)

    # compile with gfortran or ifort
    intelwin = False
    if 'win32' in sys.platform.lower():
        if fc is not None:
            if fc in ['ifort', 'mpiifort']:
                intelwin = True
        if cc is not None:
            if cc in ['cl', 'icl']:
                intelwin = True

    if intelwin:
        objext = '.obj'
    else:
        objext = '.o'

        # update openspec files
        create_openspec()

    # compile the executable
    returncode = compile(srcfiles, target, fc, cc,
                         expedite, dryrun, double, debug,
                         fflags, cflags, syslibs, arch, intelwin,
                         sharedobject)

    # create makefile
    if makefile:
        create_makefile(target, srcdir, srcdir2, extrafiles, srcfiles,
                        debug, double,
                        fc, cc, fflags, cflags, syslibs,
                        objext=objext)

    # clean up temporary files
    if makeclean and returncode == 0:
        clean(objext, intelwin)

    return returncode


if __name__ == "__main__":
    # get the arguments
    args = parser()

    # call main -- note that this form allows main to be called
    # from python as a function.
    main(args.srcdir, args.target, fc=args.fc, cc=args.cc,
         makeclean=args.makeclean, expedite=args.expedite,
         dryrun=args.dryrun, double=args.double, debug=args.debug,
         include_subdirs=args.subdirs, fflags=args.fflags,
         cflags=args.cflags, arch=args.arch, makefile=args.makefile,
         srcdir2=args.commonsrc, extrafiles=args.extrafiles,
         cmake=args.cmake)
