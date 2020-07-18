import os
import sys
import shutil
import subprocess
import pymake

# define program data
target = "gridgen"
if sys.platform.lower() == "win32":
    target += ".exe"

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join("temp")
if not os.path.exists(dstpth):
    os.makedirs(dstpth)

ver = prog_dict.version
pth = os.path.join(dstpth, prog_dict.dirname)
expth = os.path.join(pth, "examples")
exe_name = os.path.join(dstpth, target)

pm = pymake.Pymake(verbose=True)
pm.target = target
pm.appdir = dstpth
pm.cc = "g++"
pm.fc = None
pm.inplace = True


def download_src():
    # Remove the existing target download directory if it exists
    if os.path.isdir(dstpth):
        shutil.rmtree(dstpth)

    # download the target
    pm.download_target(target, download_path=dstpth)


def get_example_dirs():
    prog = os.path.abspath(exe_name)
    if os.path.isfile(prog):
        exdirs = [
            o
            for o in os.listdir(expth)
            if os.path.isdir(os.path.join(expth, o))
        ]
    else:
        exdirs = [None]
    return exdirs


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


def run_gridgen(d):
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

    prog = os.path.abspath(exe_name)
    if os.path.exists(prog):
        print("running...{}".format(d))

        testpth = os.path.join(expth, d)
        testpth = os.path.abspath(testpth)

        for cmd in biscayne_cmds:
            cmdlist = [prog] + cmd.split()
            print("running {}".format(" ".join(cmdlist)))
            retcode = run_command(cmdlist, testpth)
            success = False
            if retcode == 0:
                success = True
            assert success, "could not run {}".format(" ".join(cmdlist))

        if success:
            pymake.teardown(testpth)
    else:
        success = False

    assert success, "could not run {}".format(prog)

    return


def test_download():
    download_src()


def test_compile():
    pm.build()


def test_gridgen():
    for d in get_example_dirs():
        yield run_gridgen, d


def test_clean_up():
    clean_up()


if __name__ == "__main__":
    test_download()
    test_compile()
    for d in get_example_dirs():
        run_gridgen(d)
    test_clean_up()
