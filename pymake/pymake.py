#! /usr/bin/env python
"""
Make a binary executable for a FORTRAN program, such as MODFLOW.
"""
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
import shutil
import subprocess
import argparse
from dag import order_source_files, order_c_source_files


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
    parser.add_argument('-fc', help='Fortran compiler to use (default is gfortran)',
                        default='gfortran', choices=['ifort', 'gfortran'])
    parser.add_argument('-cc', help='C compiler to use (default is gcc)',
                        default='gcc', choices=['gcc'])
    parser.add_argument('-mc', '--makeclean', help='Clean files when done',
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
    args = parser.parse_args()
    return args

def initialize(srcdir, target):
    '''
    Remove temp source directory and target, and then copy source into
    source temp directory.  Return temp directory path.
    '''
    #remove the target if it already exists
    srcdir_temp = 'src_temp'
    objdir_temp = 'obj_temp'
    moddir_temp = 'mod_temp'

    #remove srcdir_temp and copy in srcdir
    try:
        os.remove(target)
    except:
        pass
    try:
        shutil.rmtree(srcdir_temp)
    except:
        pass
    shutil.copytree(srcdir, srcdir_temp)
    srcdir_temp = os.path.join('.', srcdir_temp)

    #if they don't exist, create directories for objects and mods
    if not os.path.exists(objdir_temp):
        os.makedirs(objdir_temp)
    if not os.path.exists(moddir_temp):
        os.makedirs(moddir_temp)

    return srcdir_temp, objdir_temp, moddir_temp

def clean(srcdir_temp, objdir_temp, moddir_temp, objext):
    '''
    Remove mod and object files, and remove the temp source directory.
    '''
    #clean things up
    print 'making clean...'
    filelist = os.listdir('.')
    delext = ['.mod', objext]
    for f in filelist:
        for ext in delext:
            if f.endswith(ext):
                os.remove(f)
    shutil.rmtree(srcdir_temp)
    shutil.rmtree(objdir_temp)
    shutil.rmtree(moddir_temp)
    return

def get_ordered_srcfiles(srcdir_temp):
    '''
    Create a list of ordered source files (both fortran and c).  Ordering
    is build using a directed acyclic graph to determine module dependencies.
    '''
    #create a list of all c(pp), f and f90 source files

    templist = []
    for path, subdirs, files in os.walk(srcdir_temp):
        for name in files:
            f = os.path.join(path, name)
            templist.append(f)

    cfiles = []  # mja
    srcfiles = []
    for f in templist:
        if f.endswith('.f') or f.endswith('.f90'):
            srcfiles.append(f)
        elif f.endswith('.c') or f.endswith('.cpp'): #mja
            cfiles.append(f)    #mja

    #orderedsourcefiles = order_source_files(srcfiles) + \
    #                     order_c_source_files(cfiles)


    srcfileswithpath = []
    for srcfile in srcfiles:
         s = os.path.join(srcdir_temp, srcfile)
         s = srcfile
         srcfileswithpath.append(s)

    #from mja
    cfileswithpath = []
    for srcfile in cfiles:
        s = os.path.join(srcdir_temp, srcfile)
        s = srcfile
        cfileswithpath.append(s)

    #order the source files using the directed acyclic graph in dag.py
    orderedsourcefiles = order_source_files(srcfileswithpath) + \
                         order_c_source_files(cfileswithpath)

    return orderedsourcefiles


def create_openspec(srcdir_temp):
    '''
    Create a new openspec.inc file that uses STREAM ACCESS.  This is specific
    to MODFLOW.
    '''
    fname = os.path.join(srcdir_temp, 'openspec.inc')
    f = open(fname, 'w')
    f.write(
'''c -- created by makebin.py
      CHARACTER*20 ACCESS,FORM,ACTION(2)
      DATA ACCESS/'STREAM'/
      DATA FORM/'UNFORMATTED'/
      DATA (ACTION(I),I=1,2)/'READ','READWRITE'/
c -- end of include file
''')
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

def compile_with_gnu(srcfiles, target, objdir_temp, moddir_temp,
                     expedite, dryrun):
    '''
    Compile the program using the gnu compilers (gfortran and gcc)
    '''
    fc = 'gfortran'
    compileflags = ['-O2']
    objext = '.o'

    #c stuff -- thanks to mja
    cc = 'gcc'
    cflags = ['-D_UF', '-O3']
    syslibs = ['-lc']

    #build object files
    objfiles = []
    for srcfile in srcfiles:
        cmdlist = []
        if srcfile.endswith('.c') or srcfile.endswith('.cpp'):        #mja
            cmdlist.append(cc)      #mja
            for switch in cflags:       #mja
                cmdlist.append(switch)      #mja
        else:           #mja
            cmdlist.append(fc)
            for switch in compileflags:
                cmdlist.append(switch)
        cmdlist.append('-c')
        cmdlist.append(srcfile)

        #object file name and location
        srcname, srcext = os.path.splitext(srcfile)
        srcname = srcname.split(os.path.sep)[-1]
        objfile = os.path.join('.', objdir_temp, srcname + '.o')
        cmdlist.append('-o')
        cmdlist.append(objfile)

        #put object files in objdir_temp
        cmdlist.append('-I' + objdir_temp)

        #put object files in objdir_temp
        cmdlist.append('-J' + moddir_temp)

        #If expedited, then check if object file is out of date (if exists).
        #No need to compile if object file is newer.
        compilefile = True
        if expedite:
            if not out_of_date(srcfile, objfile):
                compilefile = False

        #Compile
        if compilefile:
            s = ''
            for c in cmdlist:
                s += c + ' '
            print s
            if not dryrun:
                subprocess.check_call(cmdlist)

        #Save the name of the object file so that they can all be linked
        #at the end
        objfiles.append(objfile)

    #Build the link command and then link
    cmd = fc + ' '
    cmdlist = []
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
    print 'check call: ', cmdlist
    if not dryrun:
        subprocess.check_call(cmdlist)
    return

def compile_with_ifort(srcfiles, target):
    """
    Make target on Windows OS
    """

    fc = 'ifort.exe'
    cc = 'cl.exe'
    #production version compile flags
    compileflags = [
                   '-O2',
                   '-heap-arrays:0',
                   '-fpe:0',
                   '-traceback',
                   ]
    objext = '.obj'
    batchfile32 = 'compile_ia32.bat'
    batchfile64 = 'compile_x64.bat'
    try:
        os.remove(batchfile32)
    except:
        pass
    try:
        os.remove(batchfile64)
    except:
        pass

    #Create ia32
    try:
        makebatch(batchfile32, fc, compileflags, srcfiles, target, 'ia32')
        subprocess.check_call([batchfile32, ],)
    except:
        print 'Could not make ia32 target: ', target

    #Create x64
    try:
        makebatch(batchfile64, fc, compileflags, srcfiles, target, 'intel64')
        subprocess.check_call([batchfile64, ],)
    except:
        print 'Could not make x64 target: ', target

    return

def makebatch(batchfile, fc, compileflags, srcfiles, target, platform):
    '''
    Make an ifort batch file
    '''
    cpvars = os.environ.get('IFORT_COMPILER13') + 'bin/compilervars.bat'
    f = open(batchfile, 'w')
    line = 'call ' + '"' + os.path.normpath(cpvars) + '" ' + platform + '\n'
    f.write(line)

    #write commands to build object files
    for srcfile in srcfiles:
        cmd = fc + ' '
        for switch in compileflags:
            cmd += switch + ' '
        cmd += '-c' + ' '
        cmd += srcfile
        cmd += '\n'
        f.write(cmd)

    #write commands to link
    cmd = fc + ' '
    for switch in compileflags:
        cmd += switch + ' '
    cmd += '-o' + ' ' + target + ' ' + '*.obj' + '\n'
    f.write(cmd)
    f.close()
    return

def main(srcdir, target, fc, makeclean, expedite, dryrun):
    '''
    Main part of program

    '''
    #initialize
    srcdir_temp, objdir_temp, moddir_temp = initialize(srcdir, target)

    #get ordered list of files to compile
    srcfiles = get_ordered_srcfiles(srcdir_temp)

    #compile with gfortran or ifort
    if fc == 'gfortran':
        objext = '.o'
        create_openspec(srcdir_temp)
        compile_with_gnu(srcfiles, target, objdir_temp, moddir_temp,
                         expedite, dryrun)
    elif fc == 'ifort':
        objext = '.obj'
        compile_with_ifort(srcfiles, target)
    else:
        raise Exception('Unsupported compiler')

    #clean it up
    if makeclean:
        clean(srcdir_temp, objdir_temp, moddir_temp, objext)


if __name__ == "__main__":

    #get the arguments
    args = parser()

    #call main -- note that this form allows main to be called
    #from python as a function.
    main(args.srcdir, args.target, args.fc, args.makeclean, args.expedite,
         args.dryrun)
