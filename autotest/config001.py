import os
import pymake

# define urls
urls = pymake.build_urls()

# Autotest information
retain = False
program = 'mf2005'
program_previous = 'mf2005p'

prog_dict = urls[program]
progp_dict = urls[program_previous]

exclude = ('MNW2-Fig28', 'swi2ex4sww', 'testsfr2_tab', 'UZFtest2')

# Release version information
testdir = 'temp'
url_release = prog_dict.url
dir_release = os.path.join(testdir, prog_dict.dirname)
srcdir_release = os.path.join(dir_release, prog_dict.srcdir)
version_release = prog_dict.version
target_release = os.path.join(testdir, program + '_' + version_release)

# Regression version information
testdir_previous = os.path.join(testdir)
version_previous = progp_dict.version
target_previous = os.path.join(testdir, program_previous + '_' + version_previous)
url_previous = progp_dict.url
dir_previous = os.path.join(testdir_previous, progp_dict.dirname)
srcdir_previous = os.path.join(dir_previous, progp_dict.srcdir)

exdir = 'test-run'
testpaths = [os.path.join(dir_release, exdir)]
