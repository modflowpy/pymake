# pymake
Python package for compiling MODFLOW

This is a relatively simple python package for compiling MODFLOW-based programs.  The package determines the build order using a directed acyclic graph and then compiles the source files using gfortran or ifort.

pymake can be run from the command line or it can be called from within python.  

pymake includes example scripts for building MODFLOW-2005, SEAWAT, and MODFLOW-NWT using gfortran on Mac or Linux.  The scripts download the distribution file from the USGS and compiles the source into a binary executable.  The MODFLOW-NWT script does not work yet with the present version of MODFLOW-NWT due to some non-standard Fortran.  This should be fixed in future MODFLOW-NWT releases.

pymake includes code for compiling with ifort on Windows, but this has not been tested recently.

Note that if gfortran is used, the openspec.f file will be changed to:

    c -- created by pymake.py
      CHARACTER*20 ACCESS,FORM,ACTION(2)
      DATA ACCESS/'STREAM'/
      DATA FORM/'UNFORMATTED'/
      DATA (ACTION(I),I=1,2)/'READ','READWRITE'/
    c -- end of include file


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
      -dbl, --double        Force double precision
      -dbg, --debug         Create debug version
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
    pymake.main(srcdir, target, 'gfortran', makeclean=True, expedite=False, dryrun=False,
                double=False, debug=False)

