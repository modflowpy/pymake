import os

# Autotest information
testdir = 'temp'
retain = False

exclude = ('MNW2-Fig28', 'swi2ex4sww', 'testsfr2_tab')

# Release version information
url_release = 'http://water.usgs.gov/ogw/modflow/MODFLOW-2005_v1.11.00/mf2005v1_11_00_unix.zip'
dir_release = os.path.join(testdir, 'Unix')
srcdir_release = os.path.join(dir_release, 'src')
version_release = '1.11.00'
program = 'mf2005'
target_release = os.path.join(testdir, program + '_' + version_release)
exdir = 'test-run'
testpaths = [os.path.join(dir_release, exdir)]
