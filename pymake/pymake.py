#! /usr/bin/env python
"""
Make a binary executable for a FORTRAN program, such as MODFLOW.
"""
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


def parser():
    '''
    Construct the parser and return argument values
    '''
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
                                                'mpiicc', 'g++'])
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
    parser.add_argument('-cs', '--commonsrc',
                        help='''Additional directory with common source files.''',
                        default=None)
    parser.add_argument('-ef', '--extrafiles',
                        help='''List of extra source files to in the
                        compilation.  extrafiles can be either a list of files
                        or the name of a text file that contains a list of
                        files.''',
                        default=None)
    args = parser.parse_args()
    return args


def process_Popen_command(shellflg, cmdlist):
    """
    Generic function to write Popen command data to the screen

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
        print(' '.join(cmdlist))
    return


def process_Popen_communicate(stdout, stderr):
    """
    Generic function to write communication information from Popen
    to the screen

    Parameters
    ----------
    stdout : str
        string with standard output from Popen

    stderr : str
        string with standard error output from Popen

    Returns
    -------

    """
    if stdout:
        if PY3:
            stdout = stdout.decode()
        print(stdout)
    if stderr:
        if PY3:
            stderr = stderr.decode()
        print(stderr)
    return


def initialize(srcdir, target, commonsrc, extrafiles):
    '''
    Remove temp source directory and target, and then copy source into
    source temp directory.  Return temp directory path.
    '''
    # remove the target if it already exists
    srcdir_temp = os.path.join('.', 'src_temp')
    objdir_temp = os.path.join('.', 'obj_temp')
    moddir_temp = os.path.join('.', 'mod_temp')

    # remove srcdir_temp and copy in srcdir
    try:
        os.remove(target)
    except:
        pass
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
    # if extrafiles is not None:
    #     if isinstance(extrafiles, list):
    #         files = extrafiles
    #     elif os.path.isfile(extrafiles):
    #         efpth = os.path.dirname(extrafiles)
    #         with open(extrafiles, 'r') as f:
    #             files = []
    #             for line in f:
    #                 fname = line.strip().replace('\\','/')
    #                 if len(fname) > 0:
    #                     fname = os.path.abspath(os.path.join(efpth, fname))
    #                     files.append(fname)
    #     else:
    #         raise Exception('extrafiles must be either a list of files '
    #                         'or the name of a text file that contains a list'
    #                         'of files.')
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

    # set srcdir_temp
    srcdir_temp = os.path.join(srcdir_temp)

    # if they don't exist, create directories for objects and mods
    if not os.path.exists(objdir_temp):
        os.makedirs(objdir_temp)
    if not os.path.exists(moddir_temp):
        os.makedirs(moddir_temp)

    return srcdir_temp, objdir_temp, moddir_temp


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


def clean(srcdir_temp, objdir_temp, moddir_temp, objext, winifort):
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
    shutil.rmtree(srcdir_temp)
    shutil.rmtree(objdir_temp)
    shutil.rmtree(moddir_temp)
    if winifort:
        os.remove('compile.bat')
    return


def get_ordered_srcfiles(srcdir_temp, include_subdir=False):
    """
    Create a list of ordered source files (both fortran and c).  Ordering
    is build using a directed acyclic graph to determine module dependencies.
    """
    # create a list of all c(pp), f and f90 source files

    templist = []
    for path, subdirs, files in os.walk(srcdir_temp):
        for name in files:
            if not include_subdir:
                if path != srcdir_temp:
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
        s = os.path.join(srcdir_temp, srcfile)
        s = srcfile
        srcfileswithpath.append(s)

    # from mja
    cfileswithpath = []
    for srcfile in cfiles:
        s = os.path.join(srcdir_temp, srcfile)
        s = srcfile
        cfileswithpath.append(s)

    # order the source files using the directed acyclic graph in dag.py
    orderedsourcefiles = []
    if len(srcfileswithpath) > 0:
        orderedsourcefiles += order_source_files(srcfileswithpath)

    if len(cfileswithpath) > 0:
        orderedsourcefiles += order_c_source_files(cfileswithpath)

    return orderedsourcefiles


def create_openspec(srcdir_temp):
    """
    Create new openspec.inc, FILESPEC.INC, and filespec.inc files that uses
    STREAM ACCESS.  This is specific to MODFLOW and MT3D based targets.
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
    use_iso_c = False
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
    Determine if a specified flag exists

    Not all flags will be detected, for example -O2 -fbounds-check=on
    """
    # determine the gfortran command line flags available
    cmdlist = ['gfortran', '--help', '-v']
    proc = Popen(cmdlist, stdout=PIPE, stderr=PIPE)
    process_Popen_command(False, cmdlist)

    # establish communicator
    stdout, stderr = proc.communicate()
    # process_Popen_communicate(stdout, stderr)

    # catch non-zero return code
    if proc.returncode != 0:
        msg = '{} failed, status code {}\n' \
            .format(' '.join(cmdlist), proc.returncode)
        raise RuntimeError(msg)

    if PY3:
        stdout = stdout.decode()

    avail = flag in stdout
    msg = '  {} flag available: {}'.format(flag, avail)
    print(msg)

    return avail


def compile_with_gnu(srcfiles, target, fc, cc, objdir_temp, moddir_temp,
                     expedite, dryrun, double, debug, fflags, cflags, syslibs,
                     srcdir, srcdir2, extrafiles, makefile):
    """
    Compile the program using the gnu compilers (gfortran and gcc)

    """

    # For horrible windows issue
    shellflg = False
    if sys.platform == 'win32':
        shellflg = True

    # fortran compiler switches
    if debug:
        opt = '-O0'
    else:
        opt = '-O2'
    if fflags is None:
        fflags = []
    elif isinstance(fflags, str):
        fflags = fflags.split()
    # look for optimization levels in fflags
    for fflag in fflags:
        if fflag[:2] == '-O':
            if not debug:
                opt = fflag
            fflags.remove(fflag)
            break  # after first optimization (O) flag

    # set fortran flags
    if debug:
        # Debug flags
        compileflags = ['-g',
                        opt]
    else:
        compileflags = [opt]

    # add gfortran specific compiler switches
    if fc is not None:
        if debug:
            compileflags.append(['-fcheck=all',
                                 '-fbounds-check'])
            lflag = flag_available('-ffpe-trap')
            if lflag:
                compileflags.append(
                    '-ffpe-trap=overflow,zero,invalid,denormal')
        else:
            lflag = flag_available('-ffpe-summary')
            if lflag:
                compileflags.append('-ffpe-summary=overflow')
            lflag = flag_available('-ffpe-trap')
            if lflag:
                compileflags.append('-ffpe-trap=overflow,zero,invalid')

        # add fbacktrace to debug and release versions
        compileflags.append('-fbacktrace')

        # add double precision switches
        if double:
            compileflags.append('-fdefault-real-8')
            compileflags.append('-fdefault-double-8')

    objext = '.o'

    # Split all tokens by spaces
    for fflag in ' '.join(fflags).split():
        if fflag not in compileflags:
            compileflags.append(fflag)

    # C/C++ compiler switches -- thanks to mja
    if debug:
        opt = '-O0'
    else:
        opt = '-O2'

    if cflags is None:
        cflags = []
    else:
        if isinstance(cflags, str):
            cflags = cflags.split()

    # look for optimization levels in cflags
    for cflag in cflags:
        if cflag[:2] == '-O':
            if not debug:
                opt = cflag
            cflags.remove(cflag)
            break  # after first optimization (O) flag

    # set additional c flags
    if debug:
        # Debug flags
        cflags += ['-g',
                   opt]
    else:
        cflags += [opt]
    if cc.startswith('g'):
        if debug:
            lflag = flag_available('-Wall')
            if lflag:
                cflags += ['-Wall']
        else:
            pass

    # syslibs
    # reset syslibs for windows
    if sys.platform == 'win32':
        syslibs = []

    # Add -D-UF flag for C code if ISO_C_BINDING is not used in Fortran
    # code that is linked to C/C++ code
    # -D_UF defines UNIX naming conventions for mixed language compilation.
    use_iso_c = get_iso_c(srcfiles)
    if not use_iso_c:
        cflags.append('-D_UF')

    # build object files
    print('\nCompiling object files for ' +
          '{}...'.format(os.path.basename(target)))
    objfiles = []

    # assume that header files may be in other folders, so make a list
    searchdir = []
    for f in srcfiles:
        dirname = os.path.dirname(f)
        if dirname not in searchdir:
            searchdir.append(dirname)

    for srcfile in srcfiles:
        cmdlist = []
        iscfile = False
        if srcfile.endswith('.c') or srcfile.endswith('.cpp'):  # mja
            iscfile = True
            cmdlist.append(cc)  # mja
            for switch in cflags:  # mja
                cmdlist.append(switch)  # mja
        else:  # mja
            cmdlist.append(fc)
            for switch in compileflags:
                cmdlist.append(switch)

        # add search path for any header files
        for sd in searchdir:
            cmdlist.append('-I{}'.format(sd))

        cmdlist.append('-c')
        cmdlist.append(srcfile)

        # object file name and location
        srcname, srcext = os.path.splitext(srcfile)
        srcname = srcname.split(os.path.sep)[-1]
        objfile = os.path.join(objdir_temp, srcname + '.o')
        cmdlist.append('-o')
        cmdlist.append(objfile)

        if not iscfile:
            # put object files in objdir_temp
            cmdlist.append('-I' + objdir_temp)
            # put module files in moddir_temp
            cmdlist.append('-J' + moddir_temp)

        # If expedited, then check if object file is out of date (if exists).
        # No need to compile if object file is newer.
        compilefile = True
        if expedite:
            if not out_of_date(srcfile, objfile):
                compilefile = False

        # Compile
        if compilefile:
            if not dryrun:
                # subprocess.check_call(cmdlist, shell=shellflg)
                proc = Popen(cmdlist, shell=shellflg, stdout=PIPE, stderr=PIPE)
                process_Popen_command(shellflg, cmdlist)

                # establish communicator
                stdout, stderr = proc.communicate()
                process_Popen_communicate(stdout, stderr)

                # catch non-zero return code
                if proc.returncode != 0:
                    msg = '{} failed, status code {}\n' \
                        .format(' '.join(cmdlist), proc.returncode)
                    print(msg)
                    return proc.returncode

        # Save the name of the object file so that they can all be linked
        # at the end
        objfiles.append(objfile)

    # Build the link command and then link
    msg = '\nLinking object files ' + \
          'to make {}...'.format(os.path.basename(target))
    print(msg)
    cmdlist = []
    if fc is None:
        cmd = cc + ' '
        cmdlist.append(cc)
    else:
        cmd = fc + ' '
        cmdlist.append(fc)
    for switch in compileflags:
        cmd += switch + ' '
        cmdlist.append(switch)
    cmdlist.append('-o')
    cmdlist.append(os.path.join('.', target))

    for objfile in objfiles:
        cmdlist.append(objfile)

    for switch in syslibs:
        cmdlist.append(switch)

    if not dryrun:
        proc = Popen(cmdlist, shell=shellflg, stdout=PIPE, stderr=PIPE)
        process_Popen_command(shellflg, cmdlist)

        # establish communicator
        stdout, stderr = proc.communicate()
        process_Popen_communicate(stdout, stderr)

        # catch non-zero return code
        if proc.returncode != 0:
            msg = '{} failed, status code {}\n' \
                .format(' '.join(cmdlist), proc.returncode)
            print(msg)
            return proc.returncode

    # create makefile
    if makefile:
        create_makefile(target, srcdir, srcdir2, extrafiles, objfiles,
                        fc, compileflags, cc, cflags, syslibs,
                        modules=['-I', '-J'])

    # return
    return 0


def compile_with_macnix_ifort(srcfiles, target, fc, cc,
                              objdir_temp, moddir_temp,
                              expedite, dryrun, double, debug,
                              fflags, cflags, syslibs,
                              srcdir, srcdir2, extrafiles, makefile):
    """
    Make target on Mac OSX
    """
    # fortran compiler switches

    if debug:
        opt = '-O0'
    else:
        opt = '-O2'
    if fflags is None:
        fflags = []
    elif isinstance(fflags, str):
        fflags = fflags.split()

    # look for optimization levels in fflags
    for fflag in fflags:
        if fflag[:2] == '-O' or fflag == '-fast':
            if not debug:
                opt = fflag
            fflags.remove(fflag)
            break  # after first optimization (O) flag
    if debug:
        compileflags = [
            opt,
            '-debug', 'all',
            '-no-heap-arrays',
            '-fpe0',
            '-traceback'
        ]
    else:
        # production version compile flags
        compileflags = [
            opt,
            '-no-heap-arrays',
            '-fpe0',
            '-traceback'
        ]

    # add double precision compiler switches
    if double:
        compileflags += ['-real-size', '64']
        compileflags += ['-double-size', '64']

    # Split all tokens by spaces
    for fflag in ' '.join(fflags).split():
        if fflag not in compileflags:
            compileflags.append(fflag)

    # C/C++ compiler switches
    if cflags is None:
        cflags = []
    if debug:
        cflags += ['-O0', '-g']
    else:
        cflags += ['-O3']

    # Add -D-UF flag for C code if ISO_C_BINDING is not used in Fortran
    # code that is linked to C/C++ code
    # -D_UF defines UNIX naming conventions for mixed language compilation.
    use_iso_c = get_iso_c(srcfiles)
    if not use_iso_c:
        cflags.append('-D_UF')

    # build object files
    print('\nCompiling object files for ' +
          '{}...'.format(os.path.basename(target)))
    objfiles = []

    # assume that header files may be in other folders, so make a list
    searchdir = []
    for f in srcfiles:
        dirname = os.path.dirname(f)
        if dirname not in searchdir:
            searchdir.append(dirname)

    for srcfile in srcfiles:
        cmdlist = []
        if srcfile.endswith('.c') or srcfile.endswith('.cpp'):  # mja
            cmdlist.append(cc)  # mja
            for switch in cflags:  # mja
                cmdlist.append(switch)  # mja
        else:  # mja
            cmdlist.append(fc)

            # put module files in moddir_temp
            cmdlist.append('-module')
            cmdlist.append('./' + moddir_temp + '/')

            for switch in compileflags:
                cmdlist.append(switch)

        # add search path for any header files
        for sd in searchdir:
            cmdlist.append('-I{}'.format(sd))

        cmdlist.append('-c')
        cmdlist.append(srcfile)

        # object file name and location
        srcname, srcext = os.path.splitext(srcfile)
        srcname = srcname.split(os.path.sep)[-1]
        objfile = os.path.join('.', objdir_temp, srcname + '.o')
        cmdlist.append('-o')
        cmdlist.append(objfile)

        # If expedited, then check if object file is out of date (if exists).
        # No need to compile if object file is newer.
        compilefile = True
        if expedite:
            if not out_of_date(srcfile, objfile):
                compilefile = False

        # Compile
        if compilefile:
            if not dryrun:
                # subprocess.check_call(cmdlist)
                proc = Popen(cmdlist, stdout=PIPE, stderr=PIPE)
                process_Popen_command(False, cmdlist)

                # establish communicator
                stdout, stderr = proc.communicate()
                process_Popen_communicate(stdout, stderr)

                # catch non-zero return code
                if proc.returncode != 0:
                    msg = '{} failed, status code {}\n' \
                        .format(' '.join(cmdlist), proc.returncode)
                    print(msg)
                    return proc.returncode

        # Save the name of the object file so that they can all be linked
        # at the end
        objfiles.append(objfile)

    # Build the link command and then link
    print(('\nLinking object files to make ' +
           '{}...'.format(os.path.basename(target))))

    cmdlist = []
    if fc is None:
        cmd = cc + ' '
        cmdlist.append(cc)
    else:
        cmd = fc + ' '
        cmdlist.append(fc)
    for switch in compileflags:
        cmd += switch + ' '
        cmdlist.append(switch)

    for switch in compileflags:
        cmd += switch + ' '
        cmdlist.append(switch)
    cmdlist.append('-o')
    cmdlist.append(os.path.join('.', target))
    for objfile in objfiles:
        cmdlist.append(objfile)
    for switch in syslibs:
        cmdlist.append(switch)
    if not dryrun:
        # subprocess.check_call(cmdlist)
        proc = Popen(cmdlist, stdout=PIPE, stderr=PIPE)
        process_Popen_command(False, cmdlist)

        # establish communicator
        stdout, stderr = proc.communicate()
        process_Popen_communicate(stdout, stderr)

        # catch non-zero return code
        if proc.returncode != 0:
            msg = '{} failed, status code {}\n' \
                .format(' '.join(cmdlist), proc.returncode)
            print(msg)
            return proc.returncode

    # create makefile
    if makefile:
        create_makefile(target, srcdir, srcdir2, extrafiles, objfiles,
                        fc, compileflags, cc, cflags, syslibs,
                        modules=['-module '])

    # return
    return 0


def compile_with_ifort(srcfiles, target, fc, cc, objdir_temp, moddir_temp,
                       expedite, dryrun, double, debug, fflagsu, cflagsu,
                       syslibs, arch, srcdir, srcdir2, extrafiles, makefile):
    """
    Make target on Windows OS
    """

    if fc == 'ifort':
        fc = 'ifort.exe'
    elif fc is not None:
        fc = '{}.exe'.format(fc)
    if cc == 'icc':
        cc = 'icc.exe'
    elif cc == 'icl':
        cc = 'icl.exe'
    else:
        cc = 'cl.exe'

    # C/C++ compiler switches
    cflags = ['/nologo', '/c']
    # if debug:
    #    cflags += ['/O0', '/g']
    # else:
    #    cflags += ['/O3']

    fflags = ['/heap-arrays:0', '/fpe:0', '/traceback', '/nologo']
    if debug:
        opt = '/debug'
    else:
        opt = '/O2'
    if fflagsu is None:
        fflagsu = []
    elif isinstance(fflagsu, str):
        fflagsu = fflagsu.split()
    if cflagsu is None:
        cflagsu = []
    elif isinstance(cflagsu, str):
        cflagsu = cflagsu.split()
    # look for optimization levels in fflags
    for fflag in fflagsu:
        if fflag[:2] in ('-O', '/O') or fflag in ('-fast', '/fast'):
            if not debug:
                opt = fflag
            fflagsu.remove(fflag)
            break  # after first optimization (O) flag
    if debug:
        fflags.append(opt)
        cflags.append('/Zi')
    else:
        # production version compile flags
        fflags.append(opt)
        cflags.append('/O2')
    if double:
        fflags.append('/real-size:64')
        fflags.append('/double-size:64')
    # Split all tokens by spaces
    for fflag in ' '.join(fflagsu).split():
        if fflag not in fflags:
            fflags.append(fflag)
    for cflag in ' '.join(cflagsu).split():
        if cflag not in cflags:
            cflags.append(cflag)
    objext = '.obj'
    batchfile = 'compile.bat'
    if os.path.isfile(batchfile):
        try:
            os.remove(batchfile)
        except:
            pass

    # Create target
    try:
        # clean exe prior to build so that test for exe below can return a
        # non-zero error code
        if flopy_avail:
            if flopy_is_exe(target):
                os.remove(target)
        makebatch(batchfile, fc, cc, fflags, cflags, srcfiles, target,
                  arch, objdir_temp, moddir_temp)
        proc = Popen([batchfile, ], stdout=PIPE, stderr=STDOUT)
        while True:
            line = proc.stdout.readline()
            c = line.decode('utf-8')
            if c != '':
                c = c.rstrip('\r\n')
                print('{}'.format(c))
            else:
                break
        if flopy_avail:
            if not flopy_is_exe(target):
                return 1
        else:
            return 0
    except:
        print('Could not make x64 target: ', target)
        print(traceback.print_exc())

    # create makefile
    if makefile:
        print('makefile not created for Windows with Intel Compiler.')

    # return
    return 0


def makebatch(batchfile, fc, cc, fflags, cflags, srcfiles, target, arch,
              objdir_temp, moddir_temp):
    """
    Make an ifort batch file
    
    """
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
        raise Exception('Could not find cpvars: {0}'.format(cpvars))
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
            cmd = cc + ' '
            for switch in cflags:
                cmd += switch + ' '

            # add search path for any header files
            for sd in searchdir:
                cmd += '/I{} '.format(sd)

            obj = os.path.join(objdir_temp,
                               os.path.splitext(os.path.basename(srcfile))[0]
                               + '.obj')
            cmd += '/Fo' + obj + ' '
            cmd += srcfile
        else:
            cmd = fc + ' '
            for switch in fflags:
                cmd += switch + ' '
            cmd += '-c' + ' '
            cmd += '/module:{0}\ '.format(moddir_temp)
            cmd += '/object:{0}\ '.format(objdir_temp)
            cmd += srcfile
            f.write('echo ' + os.path.basename(srcfile) + '\n')
        f.write(cmd + '\n')

    # write commands to link
    if fc is None:
        cmd = cc + ' '
    else:
        cmd = fc + ' '
        for switch in fflags:
            cmd += switch + ' '
    cmd += '-o' + ' ' + target + ' ' + objdir_temp + '\*.obj' + '\n'
    f.write(cmd)
    f.close()
    return


def create_makefile(target, srcdir, srcdir2, extrafiles, objfiles,
                    fc, fflags, cc, cflags, syslibs,
                    objext='.o', modules=['-I', '-J']):
    # open makefile
    f = open('makefile', 'w')

    # write header for the make file
    f.write('# makefile created on {}\n'.format(datetime.datetime.now()) +
            '# by pymake (version {})\n'.format(__version__))
    f.write('# using the {} fortran and {} c/c++ compilers.\n'.format(fc, cc))
    f.write('\n')

    # specify directory for the executable
    f.write('# Define the directories for the object and module files,\n' +
            '# the executable, and the executable name and path.\n')
    pth = os.path.dirname(objfiles[0]).replace('\\', '/')
    f.write('OBJDIR = {}\n'.format(pth))
    pth = os.path.dirname(target).replace('\\', '/')
    if len(pth) < 1:
        pth = '.'
    f.write('BINDIR = {}\n'.format(pth))
    pth = target.replace('\\', '/')
    f.write('PROGRAM = {}\n'.format(pth))
    f.write('\n')
    dirs = [d[0].replace('\\', '/') for d in os.walk(srcdir)]
    if srcdir2 is not None:
        dirs2 = [d[0].replace('\\', '/') for d in os.walk(srcdir2)]
        dirs = dirs + dirs2
    files = parse_extrafiles(extrafiles)
    if files is not None:
        for ef in files:
            fdir = os.path.dirname(ef)
            rdir = os.path.relpath(fdir, os.getcwd())
            rdir = rdir.replace('\\', '/')
            if rdir not in dirs:
                dirs.append(rdir)
    srcdirs = []
    for idx, dir in enumerate(dirs):
        srcdirs.append('SOURCEDIR{}'.format(idx + 1))
        line = '{}={}\n'.format(srcdirs[idx], dir)
        f.write(line)
    f.write('\n')
    f.write('VPATH = \\\n')
    for idx, sd in enumerate(srcdirs):
        f.write('${' + '{}'.format(sd) + '} ')
        if idx + 1 < len(srcdirs):
            f.write('\\')
        f.write('\n')
    f.write('\n')

    ffiles = ['.f', '.f90', '.F90', '.fpp']
    cfiles = ['.c', '.cpp']
    line = '.SUFFIXES: '
    for tc in cfiles:
        line += '{} '.format(tc)
    for tf in ffiles:
        line += '{} '.format(tf)
    line += objext
    f.write('{}\n'.format(line))
    f.write('\n')

    f.write('# Define the Fortran compile flags\n')
    f.write('FC = {}\n'.format(fc))
    line = 'FFLAGS = '
    for ff in fflags:
        line += '{} '.format(ff)
    f.write('{}\n'.format(line))
    f.write('\n')

    f.write('# Define the C compile flags\n')
    f.write('CC = {}\n'.format(cc))
    line = 'CFLAGS = '
    for cf in cflags:
        line += '{} '.format(cf)
    f.write('{}\n'.format(line))
    f.write('\n')

    f.write('# Define the libraries\n')
    line = 'SYSLIBS = '
    for sl in syslibs:
        line += '{} '.format(sl)
    f.write('{}\n'.format(line))
    f.write('\n')

    f.write('OBJECTS = \\\n')
    for idx, objfile in enumerate(objfiles):
        f.write('$(OBJDIR)/{} '.format(os.path.basename(objfile)))
        if idx + 1 < len(objfiles):
            f.write('\\')
        f.write('\n')
    f.write('\n')

    f.write('# Define task functions\n')
    f.write('\n')

    f.write('# Create the bin directory and compile and link the program\n')
    f.write('all: makebin | $(PROGRAM)\n')
    f.write('\n')

    f.write('# Make the bin directory for the executable\n')
    f.write('makebin :\n')
    f.write('\tmkdir -p $(BINDIR)\n')
    f.write('\n')

    f.write('# Define the objects that make up the program\n')
    f.write('$(PROGRAM) : $(OBJECTS)\n')
    line = '\t-$(FC) $(FFLAGS) -o $@ $(OBJECTS) $(SYSLIBS) '
    for m in modules:
        line += '{}$(OBJDIR) '.format(m)
    f.write('{}\n'.format(line))
    f.write('\n')

    for tf in ffiles:
        f.write('$(OBJDIR)/%{} : %{}\n'.format(objext, tf))
        f.write('\t@mkdir -p $(@D)\n')
        line = '\t$(FC) $(FFLAGS) -c $< -o $@ '
        for m in modules:
            line += '{}$(OBJDIR) '.format(m)
        f.write('{}\n'.format(line))
        f.write('\n')

    for tc in cfiles:
        f.write('$(OBJDIR)/%.o : %{}\n'.format(tc))
        f.write('\t@mkdir -p $(@D)\n')
        line = '\t$(CC) $(CFLAGS) -c $< -o $@'
        f.write('{}\n'.format(line))
        f.write('\n')

    f.write('# Clean the object and module files and the executable\n')
    f.write('.PHONY : clean\n' +
            'clean : \n' +
            '\t-rm -rf $(OBJDIR)\n' +
            '\t-rm -rf $(PROGRAM)\n')
    f.write('\n')

    f.write('# Clean the object and module files\n')
    f.write('.PHONY : cleanobj\n' +
            'cleanobj : \n' +
            '\t-rm -rf $(OBJDIR)\n')
    f.write('\n')

    # close the make file
    f.close()


def main(srcdir, target, fc='gfortran', cc='gcc', makeclean=True,
         expedite=False, dryrun=False, double=False, debug=False,
         include_subdirs=False, fflags=None, cflags=None, syslibs='-lc',
         arch='intel64', makefile=False, srcdir2=None, extrafiles=None):
    """
    Main part of program

    """
    # initialize success
    success = 0

    # write summary information
    print('\nsource files are in:\n    {0}'.format(srcdir))
    print('executable name to be created:\n    {}'.format(target))
    if srcdir2 is not None:
        print('additional source files are in:\n     {}'.format(srcdir2))

    # make sure the path for the target exists
    pth = os.path.dirname(target)
    if pth == '':
        pth = '.'
    if not os.path.exists(pth):
        print('creating target path - {}'.format(pth))
        os.makedirs(pth)

    # initialize
    srcdir_temp, objdir_temp, moddir_temp = initialize(srcdir, target,
                                                       srcdir2, extrafiles)

    # get ordered list of files to compile
    srcfiles = get_ordered_srcfiles(srcdir_temp, include_subdirs)

    # convert syslibs to a list
    if isinstance(syslibs, str):
        syslibs = [syslibs]

    # compile with gfortran or ifort
    winifort = False
    if fc == 'gfortran' or (fc is None and cc in ['gcc', 'g++', 'clang']):
        objext = '.o'
        create_openspec(srcdir_temp)
        success = compile_with_gnu(srcfiles, target, fc, cc,
                                   objdir_temp, moddir_temp,
                                   expedite, dryrun, double, debug, fflags,
                                   cflags, syslibs, srcdir, srcdir2, extrafiles,
                                   makefile)
    elif fc == 'ifort' or fc == 'mpiifort' or \
            (fc is None and cc in ['icc', 'cl', 'icl']):
        platform = sys.platform
        if 'darwin' in platform.lower() or 'linux' in platform.lower():
            create_openspec(srcdir_temp)
            objext = '.o'
            success = compile_with_macnix_ifort(srcfiles, target, fc, cc,
                                                objdir_temp, moddir_temp,
                                                expedite, dryrun, double,
                                                debug, fflags, cflags, syslibs,
                                                srcdir, srcdir2, extrafiles,
                                                makefile)
        else:
            winifort = True
            objext = '.obj'
            # cc = 'cl.exe'
            success = compile_with_ifort(srcfiles, target, fc, cc,
                                         objdir_temp, moddir_temp,
                                         expedite, dryrun, double, debug,
                                         fflags, cflags, syslibs, arch,
                                         srcdir, srcdir2, extrafiles, makefile)
    else:
        raise Exception('Unsupported compiler')

    # Clean it up
    if makeclean:
        clean(srcdir_temp, objdir_temp, moddir_temp, objext, winifort)

    return success


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
         srcdir2=args.commonsrc, extrafiles=args.extrafiles)
