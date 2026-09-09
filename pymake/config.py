__author__ = "Joseph D. Hughes"
__date__ = "September 09, 2026"
__version__ = "2.1.0.dev0"
__maintainer__ = "Joseph D. Hughes"
__email__ = "jdhughes@usgs.gov"
__status__ = "Production"
__description__ = """\
This is the pymake program for building fortran, c, and c++ source
files, such as the source files that come with MODFLOW. The program
builds a target with the meson build system, using the build file the
target provides where there is one and writing one from the source
files it finds where there is not. A GNU makefile can be written for
the target as well, or instead of building it.
"""
