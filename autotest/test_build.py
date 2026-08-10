import os
import sys
import time
from pathlib import Path
from platform import system

import pytest
from flaky import flaky
from modflow_devtools.misc import get_ostag, set_dir
from modflow_devtools.ostags import get_binary_suffixes

import pymake

RERUNS = 1

targets = pymake.usgs_program_data.get_keys(current=True)
targets_exclude = []
test_ostag = get_ostag()
test_fc_env = os.environ.get("FC")
meson_exclude = []
if "win" in test_ostag and test_fc_env in ("ifort",):
    targets_exclude = ["gridgen"]

targets = [t for t in targets if t not in targets_exclude]
targets_meson = [t for t in targets if t not in meson_exclude]

# a target whose meson build file cannot be read, so pymake falls back to a
# generated one. each of these reads an option its build file does not
# declare, and meson stops with 'Option double does not exist'
meson_provided_unusable = ("zonbud", "zonbudusg", "mfusgt")

make_exclude = ("libmf6", "gridgen", "mf2000", "swtv4", "mflgr")
targets_make = [t for t in targets if t not in make_exclude]


def build_with_makefile(target):
    success = True
    if os.path.isfile("makefile"):
        # wait to delete on windows
        if sys.platform.lower() == "win32":
            time.sleep(6)

        # clean prior to make
        print(f"clean {target} with makefile")
        os.system("make clean")

        print(f"build {target} with makefile")
        return_code = os.system("make")

        success = os.path.isfile(target)
        if success:
            errmsg = ""
        else:
            errmsg = f"{target} created by makefile does not exist."
    else:
        errmsg = "makefile does not exist"

    return success, errmsg


@pytest.mark.base
@flaky(max_runs=RERUNS)
@pytest.mark.parametrize("target", targets)
def test_build(function_tmpdir, target: str) -> None:
    with set_dir(function_tmpdir):
        pm = pymake.Pymake(verbose=True)
        pm.target = target
        pm.inplace = True
        fc = os.environ.get("FC", "gfortran")
        assert pymake.build_apps(target, pm, verbose=True, clean=False) == 0, (
            f"could not compile {target}"
        )


@pytest.mark.base
@flaky(max_runs=RERUNS)
@pytest.mark.parametrize("target", targets_meson)
def test_meson_build(function_tmpdir, target: str) -> None:
    fc = os.environ.get("FC", "gfortran")
    cc = os.environ.get("CC", "gcc")
    pymake.linker_update_environment(cc=cc, fc=fc)
    with set_dir(function_tmpdir):
        assert pymake.build_apps(target, verbose=True, clean=False, meson=True) == 0, (
            f"could not compile {target}"
        )


@pytest.mark.base
@flaky(max_runs=RERUNS)
@pytest.mark.parametrize("target", targets_meson)
def test_meson_artifacts(function_tmpdir, target: str) -> None:
    """Check what a meson build built, and which build file built it.

    A build that returns zero says nothing about what it produced. The
    executable a target is asked for has to exist, and a build file a target
    provides has to be the one that was used, rather than being replaced by
    a generated one when it could not be read.
    """
    fc = os.environ.get("FC", "gfortran")
    cc = os.environ.get("CC", "gcc")
    pymake.linker_update_environment(cc=cc, fc=fc)
    with set_dir(function_tmpdir):
        pm = pymake.Pymake(verbose=True)
        pm.target = target
        pm.meson = True
        pm.appdir = "."
        pm.download_target(target, download_path=".")

        # a build file the target provides is read before the build, so that
        # it can be compared with the build file that was used
        provided = Path(pm.download_dir) / "meson.build"
        before = provided.read_bytes() if provided.is_file() else None

        assert pm.build() == 0, f"could not build {target}"

        ext, shared_ext = get_binary_suffixes()
        prog_data = pymake.usgs_program_data.get_target(target)
        suffix = shared_ext if prog_data.shared_object else ext
        exe = Path(function_tmpdir) / f"{target}{suffix}"
        assert exe.is_file(), f"{exe.name} was not built by meson"

        if before is not None and target not in meson_provided_unusable:
            assert provided.read_bytes() == before, (
                f"the meson build file {target} provides was replaced by a "
                "generated one, so the build fell back"
            )


@pytest.mark.base
@flaky(max_runs=RERUNS)
@pytest.mark.skipif(sys.platform == "win32", reason="do not run on Windows")
@pytest.mark.parametrize("target", targets_make)
def test_makefile_build(function_tmpdir, target: str) -> None:
    with set_dir(function_tmpdir):
        pm = pymake.Pymake(verbose=True)
        pm.target = target
        pm.makefile = True
        pm.makefiledir = "."
        pm.inplace = True
        pm.dryrun = True
        pm.makeclean = False

        pm.download_target(target)
        assert pm.download, f"could not download {target} distribution"
        assert pm.build() == 0, f"could not compile {target}"

        success, errmsg = build_with_makefile(target)
        assert success, errmsg
