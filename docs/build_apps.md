# Building Applications

The following scripts can be run directly from the command line to build
MODFLOW 6, MODFLOW-2005, MODFLOW-NWT, MODFLOW-USG, MODFLOW-LGR, MODFLOW-2000,
MODPATH 6, MODPATH 7, MT3DMS, MT3D-USGS, and SEAWAT binaries on Linux, Mac,
and Windows. The scripts will download the distribution file from the USGS 
(requires internet connection), unzip the file, and compile the source.  
MT3DMS will be downloaded from the University of Alabama and Triangle will be 
downloaded from 
[netlib.org](http://www.netlib.org/voronoi/triangle.zip). The scripts use the 
`pymake.build_apps()` method which download and unzip the distribution files 
and set all of the pymake settings required to build the program. Available 
example scripts include: 

1. `make_modflow6.py`
1. `make_mf2005.py`
1. `make_mfnwt.py`
1. `make_mfusg.py`
1. `make_mflgr.py`
1. `make_mf2000.py`
1. `make_modpath6.py`
1. `make_modpath7.py`
1. `make_gsflow.py`
1. `make_vs2dt.py`
1. `make_mt3d.py`
1. `make_mt3dusgs.py`
1. `make_swtv4.py`
1. `make_crt.py`
1. `make_gridgen.py`
1. `make_triangle.py`

Optional command line arguments can be used to customize the build (`-fc`, 
`-cc`, `--fflags`, etc.). MODFLOW 6 could be built using intel compilers and 
an `O3` optimation level by specifying:

```
python make_mf6.py -fc=ifort --fflags='-O3'
```
