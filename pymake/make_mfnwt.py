from __future__ import print_function
import os
import shutil
import pymake
from download import download_and_unzip

# Note, this script does not work yet due to some non-standard Fortran
# in one or more of the source files.

# Download the MODFLOW-NWT distribution
url = "http://water.usgs.gov/ogw/modflow-nwt/MODFLOW-NWT-v1.0.9/MODFLOW-NWT_1.0.9.zip"
download_and_unzip(url)

# Remove the parallel and serial folders from the source directory
srcdir = os.path.join('MODFLOW-NWT_1.0.9', 'src')
target = 'mfnwt'
pymake.main(srcdir, target, 'gfortran', makeclean=True, expedite=False,
            dryrun=False, double=False, debug=False)
