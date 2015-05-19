# pymake
Python package for compiling MODFLOW

This is a relatively simple python package for compiling MODFLOW-based programs.  The package determines the build order using a directed acyclic graph and then compiles the source files using gfortran or ifort.

pymake can be run from the command line or it can be called from within python.  


## Command Line Usage

To see help for running from command line, use the following statement.

    python pymake.py -h

usage: pymake.py [-h] [-fc {ifort,gfortran}] [-cc {gcc}] [-mc] [-e] [-dr]
                 srcdir target

This is the pymake program for compiling fortran source files, such as the
source files that come with MODFLOW. The program works by building a directed
acyclic graph of the module dependencies and then compiling the source files
in the proper order.

positional arguments:
  srcdir                Location of source directory
  target                Name of target to create

optional arguments:
  -h, --help            show this help message and exit
  -fc {ifort,gfortran}  Fortran compiler to use (default is gfortran)
  -cc {gcc}             C compiler to use (default is gcc)
  -mc, --makeclean      Clean files when done
  -e, --expedite        Only compile out of date source files. Clean must not
                        have been used on previous build. Does not work yet
                        for ifort.
  -dr, --dryrun         Do not actually compile. Files will be deleted, if
                        --makeclean is used. Does not work yet for ifort.

Note that the source directory should not contain any bad or duplicate source
files as all source files in the source directory will be built and linked.

## From Python

    import pymake
    srcdir = '../mfnwt/src'
    target = 'mfnwt'
    pymake.main(srcdir, target, 'gfortran', True, False, False)

