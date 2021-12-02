__author__ = "Joseph D. Hughes"
__date__ = "December 1, 2022"
__version__ = "1.2.2"
__maintainer__ = "Joseph D. Hughes"
__email__ = "jdhughes@usgs.gov"
__status__ = "Production"
__description__ = """
This is the pymake program for compiling fortran, c, and c++ source files,
such as the source files that come with MODFLOW. The program works by building
a directed acyclic graph of the module dependencies and then compiling the
source files in the proper order.
"""
