# pymake

Python package for building MODFLOW-based programs from source files.

### Version 2.1.0.dev0

[![PyPI Version](https://img.shields.io/pypi/v/mfpymake.png)](https://pypi.python.org/pypi/mfpymake)
[![Anaconda Version](https://anaconda.org/conda-forge/mfpymake/badges/version.svg)](https://anaconda.org/conda-forge/mfpymake)  
[![pymake continuous integration](https://github.com/modflowpy/pymake/workflows/pymake%20continuous%20integration/badge.svg)](https://github.com/modflowpy/pymake/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/modflowpy/pymake/branch/master/graph/badge.svg)](https://codecov.io/gh/modflowpy/pymake)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/fe4275a3cfb84acf9c84aba7b4ae2086)](https://www.codacy.com/gh/modflowpy/pymake/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=modflowpy/pymake&amp;utm_campaign=Badge_Grade)
[![Documentation Status](https://readthedocs.org/projects/mfpymake/badge/?version=latest)](https://mfpymake.readthedocs.io/en/latest/?badge=latest)  

This is a python package for building MODFLOW-based and other Fortran, C, and
C++ programs. The package downloads the source files a target is released with
and builds it with the [meson](https://mesonbuild.com/) build system, using GNU
compilers (`gcc`, `g++`, `gfortran`), Clang compilers (`clang`, `clang++`), or
the Intel compilers (`ifort`, `icl`, `icc`, `mpiifort`).

A target that is released with a meson build file is built with the build file
it provides. A target that is not is built with a build file pymake writes from
the source files it finds, which are ordered with a directed acyclic graph of
the module dependencies. A GNU makefile can be written for a target as well, or
instead of building it, with `--makefile` and `--makefile-only`.

pymake can be run from the command line or it can be called from within python.
By default, pymake sets the optimization level, Fortran flags, C/C++ flags, and
linker flags that are consistent with those used to compile MODFLOW-based
programs released by the USGS.

Note that if gfortran is used to compile MODFLOW-based codes, the `openspec.f`
and `FILESPEC.inc` (MT3DMS) files will automatically be changed to the
following so that binary files are created properly using standard Fortran:

```
c -- created by pymake_base.py
      CHARACTER*20 ACCESS,FORM,ACTION(2)
      DATA ACCESS/'STREAM'/
      DATA FORM/'UNFORMATTED'/
      DATA (ACTION(I),I=1,2)/'READ','READWRITE'/
c -- end of include file
```

## Command Line Usage

When pymake is installed, a `mfpymake` (or `mfpymake.exe` for Windows) program is installed.`mfpymake` can be used to
compile MODFLOW 6 from source files located on your computer directly from the command line using
the Intel Fortran compiler `ifort` from the root directory containing the `src` subdirectory by specifying:

```
mfpymake src/ mf6 -mc --subdirs -fc ifort
```

To see help for running from command line, use the following statement.

```
mfpymake -h
```

The help message identifies required positional arguments and optional arguments that can be provided to override
default values.

```
usage: mfpymake [-h] [-fc FC] [-cc CC] [-mc] [-dbl] [-dbg] [-sd] [-ff FFLAGS] [-cf CFLAGS]
                [-sl {-lc,-lm}] [-mf] [-dr] [-mfo] [-md MAKEFILEDIR] [-cs COMMONSRC]
                [-ef EXTRAFILES] [-exf EXCLUDEFILES] [-so] [-ad APPDIR] [-v] [--keep] [--zip ZIP]
                [--inplace] [--mesondir MESONDIR]
                srcdir target

This is the pymake program for building fortran, c, and c++ source
files, such as the source files that come with MODFLOW. The program
builds a target with the meson build system, using the build file the
target provides where there is one and writing one from the source
files it finds where there is not. A GNU makefile can be written for
the target as well, or instead of building it.

positional arguments:
  srcdir                Path source directory.
  target                Name of target to create. (can include path)

options:
  -h, --help            show this help message and exit
  -fc FC                Fortran compiler to use. A version suffix, for example gfortran-13, can be
                        included. Valid compilers are ifort, mpiifort, gfortran, and none.
                        (default is gfortran)
  -cc CC                C/C++ compiler to use. A version suffix, for example gcc-13, can be
                        included. Valid compilers are gcc, clang, clang++, icc, icl, mpiicc, g++,
                        cl, and none. (default is gcc)
  -mc, --makeclean      Clean temporary object, module, and source files when done. (default is
                        False)
  -dbl, --double        Force double precision. (default is False)
  -dbg, --debug         Create debug version. (default is False)
  -sd, --subdirs        Include source files in srcdir subdirectories. (default is None)
  -ff, --fflags FFLAGS  Additional Fortran compiler flags. Fortran compiler flags should be
                        enclosed in quotes and start with a blank space or separated from the name
                        (-ff or --fflags) with a equal sign (-ff='-O3'). (default is None)
  -cf, --cflags CFLAGS  Additional C/C++ compiler flags. C/C++ compiler flags should be enclosed
                        in quotes and start with a blank space or separated from the name (-cf or
                        --cflags) with a equal sign (-cf='-O3'). (default is None)
  -sl, --syslibs {-lc,-lm}
                        Linker system libraries. Linker libraries should be enclosed in quotes and
                        start with a blank space or separated from the name (-sl or --syslibs)
                        with a equal sign (-sl='-libgcc'). (default is None)
  -mf, --makefile       Create a GNU make makefile. (default is False)
  -dr, --dryrun         Deprecated name for --makefile-only, which replaced it when the pymake
                        build engine was removed. (default is False)
  -mfo, --makefile-only
                        Create a GNU make makefile without building the target. (default is False)
  -md, --makefiledir MAKEFILEDIR
                        GNU make makefile directory. (default is '.')
  -cs, --commonsrc COMMONSRC
                        Additional directory with common source files. (default is None)
  -ef, --extrafiles EXTRAFILES
                        List of extra source files to include in the compilation. extrafiles can
                        be either a list of files or the name of a text file that contains a list
                        of files. (default is None)
  -exf, --excludefiles EXCLUDEFILES
                        List of extra source files to exclude from the compilation. excludefiles
                        can be either a list of files or the name of a text file that contains a
                        list of files. (default is None)
  -so, --sharedobject   Create shared object or dll on Windows. (default is False)
  -ad, --appdir APPDIR  Target path that overrides path defined target path (default is None)
  -v, --verbose         Verbose output to terminal. (default is False)
  --keep                Keep existing executable. (default is False)
  --zip ZIP             Zip built executable. (default is None)
  --inplace             Source files in srcdir are used directly. (default is False)
  --mesondir MESONDIR   meson directory. (default is the directory the target is downloaded to)

Note that the source directory should not contain any bad
or duplicate source files as all source files in the source
directory, the common source file directory (srcdir2), and
the extra files (extrafiles) will be built and linked.
Files can be excluded by using the excludefiles command
line switch.

Examples:

Compile MODFLOW 6 from the root directory containing the
source files in subdirectories in the src/ subdirectory:

$ mfpymake src/ mf6 --subdirs

Compile MODFLOW 6 in the bin subdirectory using the Intel
Fortran compiler from the root directory containing the source
files in subdirectories in the the src/ subdirectory:

$ mfpymake src/ mf6 --subdirs -fc ifort --appdir bin
```

Note that command line arguments for Fortran flags, C/C++ flags, and syslib libraries should be enclosed in quotes and
start with a space prior to the first value (`-ff ' -O3'`) or use an equal sign separating the command line argument and
the values (`-ff='-O3'`). The command line argument to use an `-O3` optimization level when compiling MODFLOW 6 with
the `ifort` compiler would be:

```
mfpymake src/ mf6 -mc --subdirs -fc ifort -ff='-O3'
```

## From Python

### Script to compile MODFLOW 6

When using the pymake object (`Pymake()`) only the positional arguments
(`srcdir`, `target`) need to be specified in the script.

```python
import pymake

pm = pymake.Pymake()
pm.srcdir = "../src"
pm.target = "mf6"
pm.include_subdirs = True
pm.build()
```

It is suggested that optional variables required for successful compiling and linking be manually specified in the
script to mininimize the potential for unsuccessful builds. For MODFLOW 6, subdirectories in the `src` subdirectory need
to be included and '`pm.include_subdirs = True`' has been specified in the script. Custom optimization levels and
compiler flags could be specified to get consistent builds.

Non-default values for the optional arguments can specified as command line arguments. For example, MODFLOW 6 could be
compiled using Intel compilers instead of the default GNU compilers with the script listed above by specifying:

```
python mymf6script.py -fc ifort -cc icc
```

## Automatic Download and Build

When pymake is installed, a `make-program` (or `make-program.exe` for Windows) program is installed. `make-program` can
be used to build MODFLOW 6, MODFLOW-2005, MODFLOW-NWT, MODFLOW-USG, MODFLOW-USG Transport, MODFLOW-LGR, MODFLOW-2000,
MODPATH 6, MODPATH 7, VS2DT, MT3DMS, MT3D-USGS, SEAWAT, and SUTRA. The MODFLOW 6 shared library and the ZONEBUDGET
programs for MODFLOW 6, MODFLOW-2005 and MODFLOW-USG can be built as well, and the utility programs CRT, Triangle and
GRIDGEN. `make-program` downloads the distribution file (requires an internet connection), unzips the file, sets the
pymake settings required to build the program, and builds it with meson. Optional pymake command line arguments can be
used to customize the build (`-fc`, `-cc`, `--fflags`, etc.). For example, MODFLOW 6 could be built using intel
compilers and an `O3` optimization level by specifying:

```
make-program mf6 -fc=ifort --fflags='-O3'
```

See [pymake Read the Docs](https://mfpymake.readthedocs.io/en/1.2.4/build_apps.html#building-applications) for more
information.

## Installation

To install pymake using pip type:

```
pip install mfpymake
```

To install pymake using conda type:

```
conda install -c conda-forge mfpymake
```

To install the latest pymake release directly from the git repository type:

```
pip install https://github.com/modflowpy/pymake/zipball/master
```

To update your version of pymake with the latest development version from the git repository type:

```
pip install https://github.com/modflowpy/pymake/zipball/develop --upgrade
```
