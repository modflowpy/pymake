import os
import shutil
import subprocess
import sys

import pytest

import pymake

# use the line below to set fortran compiler using environmental variables
# if sys.platform.lower() == "win32":
#     os.environ["CC"] = "icl"
# else:
#     os.environ["CC"] = "icc"

# define program data
target = "gridgen"
if sys.platform.lower() == "win32":
    target += ".exe"

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join("temp", "t010")
if not os.path.exists(dstpth):
    os.makedirs(dstpth)

ver = prog_dict.version
pth = os.path.join(dstpth, prog_dict.dirname)
expth = os.path.join(pth, "examples", "biscayne")
exe_name = os.path.join(dstpth, target)

pm = pymake.Pymake(verbose=True)
pm.target = target
pm.appdir = dstpth
env_var = os.environ.get("CC")
if env_var is not None:
    pm.cc = env_var
else:
    pm.cc = "g++"
pm.fc = None
pm.inplace = True
pm.makeclean = True

biscayne_cmds = [
    "buildqtg action01_buildqtg.dfn",
    "grid02qtg-to-usgdata action02_writeusgdata.dfn",
    "grid01mfg-to-polyshapefile action03_shapefile.dfn",
    "grid02qtg-to-polyshapefile action03_shapefile.dfn",
    "grid01mfg-to-pointshapefile action03_shapefile.dfn",
    "grid02qtg-to-pointshapefile action03_shapefile.dfn",
    "canal_grid02qtg_lay1_intersect action04_intersect.dfn",
    "chd_grid02qtg_lay1_intersect action04_intersect.dfn",
    "grid01mfg-to-vtkfile action05_vtkfile.dfn",
    "grid02qtg-to-vtkfile action05_vtkfile.dfn",
    "grid02qtg-to-vtkfilesv action05_vtkfile.dfn",
]


def clean_up():
    # clean up
    print("Removing folder " + pth)
    if os.path.isdir(pth):
        shutil.rmtree(pth)

    # finalize pymake object
    pm.finalize()

    if os.path.isfile(exe_name):
        print("Removing " + target)
        os.remove(exe_name)
    return


def run_command(cmdlist, cwd):
    p = subprocess.Popen(
        cmdlist,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=cwd,
    )
    for line in p.stdout.readlines():
        print(line.decode().strip())
    retval = p.wait()
    return retval


def run_gridgen(cmd):
    success = False
    prog = os.path.abspath(exe_name)
    if os.path.exists(prog):
        testpth = os.path.abspath(expth)

        cmdlist = [prog] + cmd.split()
        print(f"running {' '.join(cmdlist)}")
        retcode = run_command(cmdlist, testpth)
        if retcode == 0:
            success = True

    return success


@pytest.mark.base
@pytest.mark.regression
def test_download():
    # Remove the existing target download directory if it exists
    if os.path.isdir(dstpth):
        shutil.rmtree(dstpth)

    # download the target
    pm.download_target(target, download_path=dstpth)
    assert pm.download, f"could not download {target} distribution"


@pytest.mark.base
@pytest.mark.regression
def test_compile():
    assert pm.build() == 0, f"could not compile {target}"


@pytest.mark.regression
@pytest.mark.parametrize("cmd", biscayne_cmds)
def test_gridgen(cmd):
    assert run_gridgen(cmd), f"could not run {cmd}"


@pytest.mark.base
@pytest.mark.regression
def test_clean_up():
    clean_up()


if __name__ == "__main__":
    test_download()
    test_compile()
    # for cmd in biscayne_cmds:
    #     run_gridgen(cmd)
    test_clean_up()
