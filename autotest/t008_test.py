import contextlib
import os
import shutil
import sys
import time

import flopy
import pytest

import pymake

# # define program data
# target = "mf6"
# if sys.platform.lower() == "win32":
#     target += ".exe"
#
# sharedobject_target = "libmf6"
# if sys.platform.lower() == "win32":
#     sharedobject_target += ".dll"
# elif sys.platform.lower() == "darwin":
#     sharedobject_target += ".dylib"
# else:
#     sharedobject_target += ".so"
#
# # get program dictionary
# prog_dict = pymake.usgs_program_data.get_target(target)
#
#
# # set fpth based on current path
# if os.path.basename(os.path.normpath(os.getcwd())) == "autotest":
#     fpth = os.path.abspath(
#         os.path.join("temp", "mf6examples", "mf6examples.txt")
#     )
# else:
#     fpth = os.path.abspath(
#         os.path.join("autotest", "temp", "mf6examples", "mf6examples.txt")
#     )
# if os.path.isfile(fpth):
#     with open(fpth) as f:
#         lines = f.read().splitlines()
#     sim_dirs = [line for line in lines if len(line) > 0]
# else:
#     sim_dirs = []
#
# pm = pymake.Pymake(verbose=True)
# pm.target = target
# pm.appdir = dstpth
# pm.makefile = True
# pm.makeclean = True
# pm.makefiledir = dstpth
# pm.inplace = True
# pm.networkx = True
#
#
# @contextlib.contextmanager
# def working_directory(path):
#     """Changes working directory and returns to previous on exit."""
#     prev_cwd = os.getcwd()
#     os.chdir(path)
#     try:
#         yield
#     finally:
#         os.chdir(prev_cwd)
#
#
# def build_with_makefile(makefile_target):
#     success = False
#     with working_directory(dstpth):
#         if os.path.isfile("makefile"):
#             # wait to delete on windows
#             if sys.platform.lower() == "win32":
#                 time.sleep(6)
#
#             # clean prior to make
#             print(f"clean {makefile_target} with makefile")
#             os.system("make clean")
#
#             # build MODFLOW 6 with makefile
#             print(f"build {makefile_target} with makefile")
#             return_code = os.system("make")
#
#             # test if running on Windows with ifort, if True the makefile
#             # should fail
#             if sys.platform.lower() == "win32" and pm.fc == "ifort":
#                 if return_code != 0:
#                     success = True
#                 else:
#                     success = False
#             # verify that target was made
#             else:
#                 success = os.path.isfile(makefile_target)
#
#     return success
#
#
# @pytest.mark.base
# @pytest.mark.regression
# def test_download_mf6(mf6_setup):
#     pm, dir_path, exe_path = mf6_setup
#     assert pm.download, f"failed to download {target} distribution"
#
#
# @pytest.mark.base
# @pytest.mark.regression
# def test_compile_mf6(mf6_setup):
#     pm, dir_path, exe_path = mf6_setup
#     assert pm.build() == 0, f"failed to compile {target}"
#
#
# @pytest.mark.regression
# @pytest.mark.parametrize("ws", sim_dirs)
# def test_run_mf6(mf6_setup, ws):
#     pm, dir_path, exe_path = mf6_setup
#     print(f"running model...{os.path.basename(ws)}")
#     success, buff = flopy.run_model(
#         str(exe_path), None, model_ws=ws, silent=False
#     )
#
#
# @pytest.mark.base
# @pytest.mark.regression
# def test_build_mf6_with_makefile(mf6_setup):
#     pm, dir_path, exe_path = mf6_setup
#     assert build_with_makefile(
#         target
#     ), f"failed to compile {target} with makefile"
#
#
# @pytest.mark.base
# @pytest.mark.regression
# def test_compile_mf6_sharedobject(mf6_setup, tmp_path):
#     pm, dir_path, exe_path = mf6_setup
#     pm.target = sharedobject_target
#     prog_dict = pymake.usgs_program_data.get_target(pm.target)
#     pm.appdir = tmp_path
#     pm.srcdir = os.path.join(mf6pth, prog_dict.srcdir)
#     pm.srcdir2 = os.path.join(mf6pth, "src")
#     pm.excludefiles = [os.path.join(pm.srcdir2, "mf6.f90")]
#     pm.makefile = True
#     pm.makeclean = True
#     pm.sharedobject = True
#     pm.inplace = True
#     pm.dryrun = False
#     assert pm.build() == 0, f"failed to compile {pm.target}"
#
#
# @pytest.mark.base
# @pytest.mark.regression
# def test_sharedobject_makefile():
#     assert build_with_makefile(
#         sharedobject_target
#     ), f"failed to compile {sharedobject_target} with makefile"
#