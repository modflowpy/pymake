from __future__ import print_function
import os
import sys
import shutil
import subprocess
import pymake

# define program data
target = 'gridgen'
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join('temp')
if not os.path.exists(dstpth):
    os.makedirs(dstpth)

ver = prog_dict.version
pth = os.path.join(dstpth, prog_dict.dirname)
expth = os.path.join(pth, 'examples')
exe_name = os.path.join(dstpth, target)


def get_example_dirs():
    exdirs = [o for o in os.listdir(expth)
              if os.path.isdir(os.path.join(expth, o))]
    return exdirs


def compile_code():
    # Remove the existing mf6 directory if it exists
    if os.path.isdir(pth):
        shutil.rmtree(pth)

    # compile gridgen
    pymake.usgs_program_data().list_targets(current=True)
    replace_function = pymake.build_replace(target)
    pymake.build_program(target=target, fc=None, cc='g++',
                         include_subdirs=True,
                         download_dir=dstpth,
                         exe_dir=dstpth,
                         replace_function=replace_function)


def clean_up():
    # clean up
    print('Removing folder ' + pth)
    shutil.rmtree(pth)

    ext = ''
    if sys.platform == 'win32':
        ext = '.exe'

    print('Removing ' + target)
    os.remove(exe_name + ext)
    return


def run_command(cmdlist, cwd):
    p = subprocess.Popen(cmdlist, shell=False, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, cwd=cwd)
    for line in p.stdout.readlines():
        print(line.decode().strip())
    retval = p.wait()
    return retval


def run_gridgen(d):
    print('running...{}'.format(d))

    biscayne_cmds = [
        'buildqtg action01_buildqtg.dfn',
        'grid02qtg-to-usgdata action02_writeusgdata.dfn',
        'grid01mfg-to-polyshapefile action03_shapefile.dfn',
        'grid02qtg-to-polyshapefile action03_shapefile.dfn',
        'grid01mfg-to-pointshapefile action03_shapefile.dfn',
        'grid02qtg-to-pointshapefile action03_shapefile.dfn',
        'canal_grid02qtg_lay1_intersect action04_intersect.dfn',
        'chd_grid02qtg_lay1_intersect action04_intersect.dfn',
        'grid01mfg-to-vtkfile action05_vtkfile.dfn',
        'grid02qtg-to-vtkfile action05_vtkfile.dfn',
        'grid02qtg-to-vtkfilesv action05_vtkfile.dfn', ]

    testpth = os.path.join(expth, d)
    testpth = os.path.abspath(testpth)
    prog = os.path.abspath(exe_name)

    for cmd in biscayne_cmds:
        cmdlist = [prog] + cmd.split()
        print('running ', cmdlist)
        retcode = run_command(cmdlist, testpth)
        success = False
        if retcode == 0:
            success = True
        assert success

    if success:
        pymake.teardown(testpth)
    assert success is True

    return


def test_compile():
    compile_code()


def test_gridgen():
    # get name files and simulation name
    example_dirs = get_example_dirs()
    # run models
    for d in example_dirs:
        yield run_gridgen, d


def test_clean_up():
    yield clean_up


if __name__ == "__main__":

    # compile gridgen
    compile_code()

    # get name files and simulation name
    example_dirs = get_example_dirs()

    # run models
    for d in example_dirs:
        run_gridgen(d)

    # clean up
    clean_up()
