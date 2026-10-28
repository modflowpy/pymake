"""Tests for statically linking the intel fortran runtime by default.

test_mp7.py and test_mf2005.py check the executables they build actually
come out static; these check the build file and switches that get them there.
"""

import pytest

from pymake.utils._compiler_switches import _get_linker_flags
from pymake.utils._meson_build import _create_main_meson_build


def _meson_build_text(tmp_path, srcfiles, cc):
    srcdir = tmp_path / "src"
    meson_file, _, _ = _create_main_meson_build(
        str(tmp_path),
        str(tmp_path / "hello"),
        [str(srcdir / f) for f in srcfiles],
        False,
        False,
        "ifort",
        cc,
        [],
        [],
        [],
        False,
        {"main": str(srcdir)},
        False,
    )
    return meson_file.read_text()


@pytest.fixture
def srcdir(tmp_path):
    srcdir = tmp_path / "src"
    srcdir.mkdir()
    (srcdir / "main.f90").write_text("      program main\n      end\n")
    (srcdir / "util.c").write_text("int util(void) { return 0; }\n")
    return srcdir


@pytest.mark.base
def test_link_language_omitted_for_single_language_target(tmp_path, srcdir) -> None:
    # link_language makes meson add a dynamic -lifcore/-limf
    text = _meson_build_text(tmp_path, ["main.f90"], None)
    assert "link_language" not in text


@pytest.mark.base
def test_link_language_kept_for_mixed_language_target(tmp_path, srcdir) -> None:
    text = _meson_build_text(tmp_path, ["main.f90", "util.c"], "icc")
    assert "link_language: 'fortran'" in text


@pytest.mark.base
@pytest.mark.parametrize("fc", ["ifort", "ifx"])
def test_mixed_language_executable_forced_static(fc) -> None:
    # meson's dynamic -lifcore/-limf land after these, so the static
    # archives have to be bracketed here to win
    _, flags = _get_linker_flags(
        "mixedmain",
        fc,
        "icc",
        [],
        ["main.f90", "util.c"],
        sharedobject=False,
        osname="linux",
        meson=True,
    )

    assert "-static-intel" in flags
    assert (
        flags.index("-Wl,-Bstatic")
        < flags.index("-lifcore")
        < flags.index("-limf")
        < flags.index("-Wl,-Bdynamic")
    )


@pytest.mark.base
def test_mixed_language_classic_makefile_not_forced_static() -> None:
    # a makefile has no link_language override to counteract
    _, flags = _get_linker_flags(
        "mixedmain",
        "ifort",
        "icc",
        [],
        ["main.f90", "util.c"],
        sharedobject=False,
        osname="linux",
    )

    assert "-Wl,-Bstatic" not in flags


@pytest.mark.base
def test_gfortran_unaffected() -> None:
    _, flags = _get_linker_flags(
        "mixedmain",
        "gfortran",
        "gcc",
        [],
        ["main.f90", "util.c"],
        sharedobject=False,
        osname="linux",
        meson=True,
    )

    assert "-static-intel" not in flags
    assert "-Wl,-Bstatic" not in flags
