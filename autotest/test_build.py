import os
import sys
import time
from pathlib import Path

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
@pytest.mark.parametrize("target", targets_meson)
def test_meson_build(function_tmpdir, target: str) -> None:
    fc = os.environ.get("FC", "gfortran")
    cc = os.environ.get("CC", "gcc")
    pymake.linker_update_environment(cc=cc, fc=fc)
    with set_dir(function_tmpdir):
        assert pymake.build_apps(target, verbose=True, clean=False) == 0, (
            f"could not compile {target}"
        )


@pytest.mark.base
@flaky(max_runs=RERUNS)
@pytest.mark.parametrize("verbose", (True, False))
def test_meson_provided_kept(function_tmpdir, verbose: bool) -> None:
    """A meson build file a target provides is kept when temporary files are
    cleaned up.

    The build file was removed with the files pymake writes, and only when
    verbose was set, so a clean build of a target that provides one left it
    without the build file it came with.
    """
    fc = os.environ.get("FC", "gfortran")
    cc = os.environ.get("CC", "gcc")
    pymake.linker_update_environment(cc=cc, fc=fc)
    with set_dir(function_tmpdir):
        pm = pymake.Pymake(verbose=verbose)
        pm.target = "zonbud"
        pm.makeclean = True
        pm.appdir = "."
        pm.download_target("zonbud", download_path="temp")

        provided = Path(pm.download_dir) / "meson.build"
        assert provided.is_file(), "zonbud does not provide a meson build file"
        before = provided.read_bytes()

        assert pm.build() == 0, "could not build zonbud"
        assert provided.is_file(), (
            "the meson build file zonbud provides was removed when the "
            "temporary files were cleaned up"
        )
        assert provided.read_bytes() == before, (
            "the meson build file zonbud provides was replaced"
        )


@pytest.mark.base
@flaky(max_runs=RERUNS)
def test_meson_mesondir(function_tmpdir) -> None:
    """A mesondir that was asked for is used rather than the download directory.

    The default was the current directory, so a mesondir of '.' could not be
    told apart from one that was not set and was replaced.
    """
    fc = os.environ.get("FC", "gfortran")
    cc = os.environ.get("CC", "gcc")
    pymake.linker_update_environment(cc=cc, fc=fc)
    with set_dir(function_tmpdir):
        pm = pymake.Pymake(verbose=True)
        pm.target = "triangle"
        pm.mesondir = "."
        pm.appdir = "."
        pm.download_target("triangle", download_path="temp")

        assert pm.build() == 0, "could not build triangle"
        assert pm.mesondir == ".", (
            f"the mesondir that was asked for ('.') was replaced by '{pm.mesondir}'"
        )

        ext, _ = get_binary_suffixes()
        exe = Path(function_tmpdir) / f"triangle{ext}"
        assert exe.is_file(), f"{exe.name} was not built by meson"


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

        if before is not None:
            assert provided.read_bytes() == before, (
                f"the meson build file {target} provides was replaced by a "
                "generated one, so the build fell back"
            )


@pytest.mark.base
def test_makefile_path() -> None:
    """A path written to a makefile uses a forward slash separator.

    The conversion only does anything on Windows, where a path is separated
    by a backslash, so the windows flavour of Path is used to check it rather
    than the one for the operating system the test runs on.
    """
    from pathlib import PureWindowsPath

    from pymake.pymake_base import _makefile_path

    for pth, expected in (
        (PureWindowsPath(r"temp\obj_temp"), "temp/obj_temp"),
        (PureWindowsPath(r"..\..\bin"), "../../bin"),
        (PureWindowsPath("."), "."),
        ("a/b", "a/b"),
    ):
        assert _makefile_path(pth) == expected, (
            f"{pth} was written as {_makefile_path(pth)} rather than {expected}"
        )


@pytest.mark.base
@flaky(max_runs=RERUNS)
@pytest.mark.skipif(sys.platform == "win32", reason="do not run on Windows")
@pytest.mark.parametrize("target", targets_make)
def test_makefile_build(function_tmpdir, target: str) -> None:
    with set_dir(function_tmpdir):
        pm = pymake.Pymake(verbose=True)
        pm.target = target
        pm.makefile_only = True
        pm.makefiledir = "."
        pm.inplace = True
        pm.makeclean = False

        pm.download_target(target)
        assert pm.download, f"could not download {target} distribution"
        assert pm.build() == 0, f"could not compile {target}"

        success, errmsg = build_with_makefile(target)
        assert success, errmsg
