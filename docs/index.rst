.. pymake documentation master file, created by
   sphinx-quickstart on Wed Aug 19 13:52:39 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

pymake Documentation
==================================
This is a python package for compiling MODFLOW-based and other Fortran, C, and
C++ programs. The package determines the build order using a directed acyclic
graph and then compiles the source files using GNU compilers (:code:`gcc`,
:code:`g++`, :code:`gfortran`) or Intel compilers (:code:`ifort`, :code:`icc`).

pymake can be run from the command line or it can be called from within python.
By default, pymake sets the optimization level, Fortran flags, C/C++ flags, and
linker flags that are consistent with those used to compile MODFLOW-based
programs released by the USGS.

pymake includes example scripts for building MODFLOW 6, MODFLOW-2005,
MODFLOW-NWT, MODFLOW-USG, MODFLOW-LGR, MODFLOW-2000, MODPATH 6, MODPATH 7,
VS2DT, MT3DMS, MT3D-USGS, and SEAWAT. Example scripts for
creating the utility programs CRT, Triangle, and GRIDGEN are also included.
The scripts download the distribution file from the USGS (and other
organizations) and compile the source into a binary executable.

The main documentation for the site is organized into the following sections:

.. toctree::
   :maxdepth: 2
   :name: pymake-learn

   Getting Started <getting_started>

.. toctree::
   :maxdepth: 2
   :name: pymake-install

   pymake Installation <installation>

.. toctree::
   :maxdepth: 2
   :name: pymake-build

   Building Applications <build_apps>


.. toctree::
   :maxdepth: 4
   :name: pymake-api

   API Documentation <api_index>


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
