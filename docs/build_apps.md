# Building Applications

When pymake is installed, a `make-program` (or `make-program.exe` for Windows) program is installed, which is usually
installed to a directory in the PATH (depending on the Python setup). From a console a list of command line arguments
and options can be determined by executing:

```console
$ make-program --help

usage: make-program [-h] [--release_precision]
                    [-fc {ifort,mpiifort,gfortran,none}]
                    [-cc {gcc,clang,clang++,icc,icl,mpiicc,g++,cl,none}] [-dr]
                    [-ff FFLAGS] [-cf CFLAGS] [-ad APPDIR] [-v] [--keep]
                    [--zip ZIP] [--meson]
                    targets

Download and build USGS MODFLOW and related programs.

positional arguments:
  targets               Program(s) to build. Options: crt, gridgen, libmf6,
                        mf2000, mf2005, mf6, mflgr, mfnwt, mfusg, mfusg_gsi,
                        mp6, mp7, mt3dms, mt3dusgs, sutra, swtv4, triangle,
                        vs2dt, zbud6, zonbud3, zonbudusg, :. Specifying the
                        target to be ':' will build all of the programs.

optional arguments:
  -h, --help            show this help message and exit
  --release_precision   If release_precision is False, then the release
                        precision version will be compiled along with a double
                        precision version of the program for programs where
                        the standard_switch and double_switch in
                        usgsprograms.txt is True. default is True.
  -fc {ifort,mpiifort,gfortran,none}
                        Fortran compiler to use. (default is gfortran)
  -cc {gcc,clang,clang++,icc,icl,mpiicc,g++,cl,none}
                        C/C++ compiler to use. (default is gcc)
  -dr, --dryrun         Do not actually compile. Files will be deleted, if
                        --makeclean is used. Does not work yet for ifort.
                        (default is False)
  -ff FFLAGS, --fflags FFLAGS
                        Additional Fortran compiler flags. Fortran compiler
                        flags should be enclosed in quotes and start with a
                        blank space or separated from the name (-ff or
                        --fflags) with a equal sign (-ff='-O3'). (default is
                        None)
  -cf CFLAGS, --cflags CFLAGS
                        Additional C/C++ compiler flags. C/C++ compiler flags
                        should be enclosed in quotes and start with a blank
                        space or separated from the name (-cf or --cflags)
                        with a equal sign (-cf='-O3'). (default is None)
  -ad APPDIR, --appdir APPDIR
                        Target path that overides path defined target path
                        (default is None)
  -v, --verbose         Verbose output to terminal. (default is False)
  --keep                Keep existing executable. (default is False)
  --zip ZIP             Zip built executable. (default is False)
  --meson               Use meson to build executable. (default is False)

Examples:

  Download and compile MODFLOW 6 in the current directory:
    $ make-program mf6

  Download and compile triangle in the ./temp subdirectory:
    $ make-program triangle --appdir temp

  Download and compile all programs in the ./temp subdirectory:
    $ make-program : --appdir temp

```

`make-program` can be used to build MODFLOW 6, MODFLOW-2005, MODFLOW-NWT, MODFLOW-USG, MODFLOW-LGR, MODFLOW-2000,
MODPATH 6, MODPATH 7, GSFLOW, VS2DT, MT3DMS, MT3D-USGS, SEAWAT, GSFLOW, PRMS, and SUTRA. Utility programs CRT, Triangle,
and GRIDGEN can also be built. `make-program` downloads the distribution file from the USGS (requires internet
connection), unzips the distribution file, sets the pymake settings required to build the program, and compiles the
source files to build the program. MT3DMS will be downloaded from the University of Alabama and Triangle will be
downloaded from [netlib.org](http://www.netlib.org/voronoi/triangle.zip). Optional command line arguments can be used to
customize the build (`-fc`, `-cc`, `--fflags`, etc.). For example, MODFLOW 6 could be built using intel compilers and
an `O3` optimation level by specifying:

```console
make-program mf6 -fc=ifort --fflags='-O3'
```