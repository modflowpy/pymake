# pymake

Python package for compiling MODFLOW-based programs.

### Version 1.2.4

![pymake continuous integration](https://github.com/modflowpy/pymake/workflows/pymake%20continuous%20integration/badge.svg)
[![codecov](https://codecov.io/gh/modflowpy/pymake/branch/master/graph/badge.svg)](https://codecov.io/gh/modflowpy/pymake)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/fe4275a3cfb84acf9c84aba7b4ae2086)](https://www.codacy.com/gh/modflowpy/pymake/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=modflowpy/pymake&amp;utm_campaign=Badge_Grade)
[![Documentation Status](https://readthedocs.org/projects/mfpymake/badge/?version=latest)](https://mfpymake.readthedocs.io/en/latest/?badge=latest)
[![PyPI Version](https://img.shields.io/pypi/v/mfpymake.png)](https://pypi.python.org/pypi/mfpymake)

This is a python package for compiling MODFLOW-based and other Fortran, C, and
C++ programs. The package determines the build order using a directed acyclic
graph and then compiles the source files using GNU compilers (`gcc`, `g++`,
`gfortran`), Clang compilers (`clang`, `clang++`), Intel compilers (`ifort`, 
`icl`, `icc`, `mpiifort`), or the CRAY Fortran compiler (`ftn`).

pymake can be run from the command line or it can be called from within python.
By default, pymake sets the optimization level, Fortran flags, C/C++ flags, and
linker flags that are consistent with those used to compile MODFLOW-based
programs released by the USGS.

pymake includes example scripts for building MODFLOW 6, MODFLOW-2005,
MODFLOW-NWT, MODFLOW-USG, MODFLOW-LGR, MODFLOW-2000, MODPATH 6, MODPATH 7,
GSFLOW, VS2DT, MT3DMS, MT3D-USGS, SEAWAT, and SUTRA. Example scripts for
creating the utility programs CRT, Triangle, and GRIDGEN are also included. The
scripts download the distribution file from the USGS (and other organizations)
and compile the source into a binary executable.

Note that if gfortran is used to compile MODFLOW-based codes, the `openspec.f`
and `FILESPEC.inc` (MT3DMS) files will automatically be changed to the
following so that binary files are created properly using standard Fortran:

```
c -- created by pymake.py
CHARACTER*20 ACCESS,FORM,ACTION(2)
DATA ACCESS/'STREAM'/
DATA FORM/'UNFORMATTED'/
DATA (ACTION(I),I=1,2)/'READ','READWRITE'/
c -- end of include file
```

## Command Line Usage

pymake can be used to compile MODFLOW 6 directly from the command line using
the Intel Fortran compiler `ifort` from a subdirectory at the same level as
the `src` subdirectory by specifying:

```
python -m pymake ../src/ ../bin/mf6 -mc --subdirs -fc ifort
```

To see help for running from command line, use the following statement.

```
python -m pymake -h
```

The help message identifies required positional arguments and optional
arguments that can be provided to overide default values.

```
usage: __main__.py [-h] [-fc {ifort,mpiifort,gfortran,ftn,none}] [-cc {gcc,clang,clang++,icc,icl,mpiicc,g++,cl,none}] [-ar {ia32,ia32_intel64,intel64}] [-mc] [-dbl] [-dbg] [-e] [-dr] [-sd] [-ff FFLAGS] [-cf CFLAGS] [-sl {-lc,-lm}] [-mf] [-md] [-cs COMMONSRC] [-ef EXTRAFILES] [-exf EXCLUDEFILES] [-so]
                   [-ad APPDIR] [-v] [--keep] [--zip ZIP] [--inplace] [--networkx] [--mb] [-mbd]
                   srcdir target

This is the pymake program for compiling fortran, c, and c++ source files, such as the source files that come with MODFLOW. The program works by building a directed acyclic graph of the module dependencies and then compiling the source files in the proper order.

positional arguments:
  srcdir                Path source directory.
  target                Name of target to create. (can include path)

optional arguments:
  -h, --help            show this help message and exit
  -fc {ifort,mpiifort,gfortran,ftn,none}
                        Fortran compiler to use. (default is gfortran)
  -cc {gcc,clang,clang++,icc,icl,mpiicc,g++,cl,none}
                        C/C++ compiler to use. (default is gcc)
  -ar {ia32,ia32_intel64,intel64}, --arch {ia32,ia32_intel64,intel64}
                        Architecture to use for Intel and Microsoft compilers on Windows. (default is intel64)
  -mc, --makeclean      Clean temporary object, module, and source files when done. (default is False)
  -dbl, --double        Force double precision. (default is False)
  -dbg, --debug         Create debug version. (default is False)
  -e, --expedite        Only compile out of date source files. Clean must not have been used on previous build. (default is False)
  -dr, --dryrun         Do not actually compile. Files will be deleted, if --makeclean is used. Does not work yet for ifort. (default is False)
  -sd, --subdirs        Include source files in srcdir subdirectories. (default is None)
  -ff FFLAGS, --fflags FFLAGS
                        Additional Fortran compiler flags. Fortran compiler flags should be enclosed in quotes and start with a blank space or separated from the name (-ff or --fflags) with a equal sign (-ff='-O3'). (default is None)
  -cf CFLAGS, --cflags CFLAGS
                        Additional C/C++ compiler flags. C/C++ compiler flags should be enclosed in quotes and start with a blank space or separated from the name (-cf or --cflags) with a equal sign (-cf='-O3'). (default is None)
  -sl {-lc,-lm}, --syslibs {-lc,-lm}
                        Linker system libraries. Linker libraries should be enclosed in quotes and start with a blank space or separated from the name (-sl or --syslibs) with a equal sign (-sl='-libgcc'). (default is None)
  -mf, --makefile       Create a GNU make makefile. (default is False)
  -md, --makefile-dir   GNU make makefile directory. (default is '.')
  -cs COMMONSRC, --commonsrc COMMONSRC
                        Additional directory with common source files. (default is None)
  -ef EXTRAFILES, --extrafiles EXTRAFILES
                        List of extra source files to include in the compilation. extrafiles can be either a list of files or the name of a text file that contains a list of files. (default is None)
  -exf EXCLUDEFILES, --excludefiles EXCLUDEFILES
                        List of extra source files to exclude from the compilation. excludefiles can be either a list of files or the name of a text file that contains a list of files. (default is None)
  -so, --sharedobject   Create shared object or dll on Windows. (default is False)
  -ad APPDIR, --appdir APPDIR
                        Target path that overides path defined target path (default is None)
  -v, --verbose         Verbose output to terminal. (default is False)
  --keep                Keep existing executable. (default is False)
  --zip ZIP             Zip built executable. (default is False)
  --inplace             Source files in srcdir are used directly. (default is False)
  --networkx            Use networkx package to build Directed Acyclic Graph use to determine the order source files are compiled in. (default is False)
  --mb, --meson-build   Use meson to build executable. (default is False)
  -mbd, --mesonbuild-dir
                        meson directory. (default is '.')

Note that the source directory should not contain any bad or duplicate source files as all source files in the source directory, the common source file directory (srcdir2), and the extra files (extrafiles) will be built and linked. Files can be excluded by using the excludefiles command line switch.
```

Note that command line arguments for Fortran flags, C/C++ flags, and syslib
libraries should be enclosed in quotes and start with a space prior to the
first value (`-ff ' -O3'`) or use an equal sign separating the command line
argument and the values (`-ff='-O3'`). The command line argument to use an
`-O3` optimization level when compiling MODFLOW 6 with the `ifort` compiler
would be:

```
python -m pymake ../src/ ../bin/mf6 -mc --subdirs -fc ifort -ff='-O3'
```

## From Python

### Script to compile MODFLOW 6

When using the pymake object (`Pymake()`) only the positional arguments
(`srcdir`, `target`) need to be specified in the script.

```python
import pymake

pm = pymake.Pymake()
pm.srcdir = '../src'
pm.target = 'mf6'
pm.include_subdirs = True
pm.build()
```

It is suggested that optional variables required for successful compiling and
linking be manually specified in the script to mininimize the potential for
unsuccessful builds. For MODFLOW 6, subdirectories in the `src` subdirectory
need to be included and '`pm.include_subdirs = True`' has been specified in the
script. Custom optimization levels and compiler flags could be specified to get
consistent builds.

Non-default values for the optional arguments can specified as command line
arguments. For example, MODFLOW 6 could be compiled using Intel compilers
instead of the default GNU compilers with the script listed above by
specifying:

```
python mymf6script.py -fc ifort -cc icc
```

## Automatic Download and Build

The following scripts can be run directly from the command line to build
MODFLOW 6, MODFLOW-2005, MODFLOW-NWT, MODFLOW-USG, MODFLOW-LGR, MODFLOW-2000,
MODPATH 6, MODPATH 7, MT3DMS, MT3D-USGS, and SEAWAT binaries on Linux, Mac, and
Windows. The scripts will download the distribution file from the USGS
(requires internet connection), unzip the file, and compile the source.  
MT3DMS will be downloaded from the University of Alabama and Triangle will be
downloaded from
[netlib.org](http://www.netlib.org/voronoi/triangle.zip). The scripts use the
`pymake.build_apps()` method which download and unzip the distribution files
and set all of the pymake settings required to build the program. Available
example scripts include:

* `make_modflow6.py`
* `make_mf2005.py`
* `make_mfnwt.py`
* `make_mfusg.py`
* `make_mflgr.py`
* `make_mf2000.py`
* `make_modpath6.py`
* `make_modpath7.py`
* `make_prms.py`
* `make_gsflow.py`
* `make_vs2dt.py`
* `make_mt3d.py`
* `make_mt3dusgs.py`
* `make_swtv4.py`
* `make_crt.py`
* `make_gridgen.py`
* `make_triangle.py`

Optional command line arguments can be used to customize the build (`-fc`,
`-cc`, `--fflags`, etc.). MODFLOW 6 could be built using intel compilers and
an `O3` optimation level by specifying:

```
python make_mf6.py -fc=ifort --fflags='-O3'
```

## Installation

To install pymake using pip type:

```
pip install mfpymake
```

To install pymake directly from the git repository type:

```
pip install https://github.com/modflowpy/pymake/zipball/master
```

To update your version of pymake with the latest from the git repository type:

```
pip install https://github.com/modflowpy/pymake/zipball/master --upgrade
```
