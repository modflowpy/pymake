import os

# Autotest information
retain = False
program = 'mf2005'
program_previous = 'mf2005'

exclude = ('MNW2-Fig28', 'swi2ex4sww', 'testsfr2_tab')

# Release version information
testdir = 'temp'
url_release = 'http://water.usgs.gov/ogw/modflow/MODFLOW-2005_v1.11.00/mf2005v1_11_00_unix.zip'
dir_release = os.path.join(testdir, 'Unix')
srcdir_release = os.path.join(dir_release, 'src')
version_release = '1.11.00'
target_release = os.path.join(testdir, program + '_' + version_release)

# Regression version information
testdir_previous = os.path.join(testdir)
version_previous = 'x.x.x'
target_previous = os.path.join(testdir, program_previous + '_' + version_previous)
url_previous = 'http://water.usgs.gov/ogw/modflow/MODFLOW-2005_v1.11.00/mf2005v1_11_00_unix.zip'
dir_previous = os.path.join(testdir_previous, 'reference')
srcdir_previous = os.path.join(dir_previous, 'src')

exdir = 'test-run'
testpaths = [os.path.join(dir_release, exdir)]
