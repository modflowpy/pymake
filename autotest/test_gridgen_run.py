import os
import pathlib as pl
import shutil
import subprocess
import sys

import pytest
from flaky import flaky

import pymake

RERUNS = 3

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
dstpth = pl.Path(f"temp_{os.path.basename(__file__).replace('.py', '')}")
dstpth.mkdir(parents=True, exist_ok=True)

ver = prog_dict.version
pth = dstpth / prog_dict.dirname
expth = pth / "examples/biscayne"
exe_name = dstpth / target

pm = pymake.Pymake(verbose=True)
pm.target = target
pm.appdir = str(dstpth)
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
    print("Removing test files and directories")

    # finalize pymake object
    pm.finalize()

    if os.path.isfile(exe_name):
        print(f"Removing {target}")
        os.remove(exe_name)

    print(f"Removing folder {pth}")
    if pth.is_dir():
        shutil.rmtree(pth)

    dirs_temp = [dstpth]
    for d in dirs_temp:
        if d.is_dir():
            shutil.rmtree(d)

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


@pytest.mark.skip
@flaky(max_runs=RERUNS)
def test_download():
    # Remove the existing target download directory if it exists
    if dstpth.is_dir():
        shutil.rmtree(dstpth)

    # download the target
    pm.download_target(target, download_path=dstpth)
    assert pm.download, f"could not download {target} distribution"


@pytest.mark.skip
def test_compile():
    assert pm.build() == 0, f"could not compile {target}"


@pytest.mark.skip
@pytest.mark.parametrize("cmd", biscayne_cmds)
def test_gridgen(cmd):
    assert run_gridgen(cmd), f"could not run {cmd}"


@pytest.mark.skip
def test_clean_up():
    clean_up()


if __name__ == "__main__":
    test_download()
    test_compile()
    # for cmd in biscayne_cmds:
    #     run_gridgen(cmd)
    test_clean_up()
