"""Tests for statically linking the intel fortran runtime by default."""

import pytest

from pymake.utils._compiler_switches import _get_linker_flags
from pymake.utils._meson_build import _create_main_meson_build


@pytest.mark.base
@pytest.mark.parametrize("osname", ["linux", "darwin"])
def test_static_intel_default_executable(osname) -> None:
    _, flags = _get_linker_flags(
        "mp7", "ifort", None, [], ["main.f90"], sharedobject=False, osname=osname
    )

    assert "-static-intel" in flags


@pytest.mark.base
def test_static_intel_default_sharedobject() -> None:
    _, flags = _get_linker_flags(
        "libmf6", "ifort", None, [], ["main.f90"], sharedobject=True, osname="linux"
    )

    assert "-static-intel" in flags


@pytest.mark.base
def test_gfortran_unaffected() -> None:
    _, flags = _get_linker_flags(
        "mp7", "gfortran", None, [], ["main.f90"], sharedobject=False, osname="linux"
    )

    assert "-static-intel" not in flags


@pytest.mark.base
def test_link_language_omitted_for_single_language_target(tmp_path) -> None:
    srcdir = tmp_path / "src"
    srcdir.mkdir()
    main = srcdir / "main.f90"
    main.write_text("      program main\n      end\n")

    meson_file, _, _ = _create_main_meson_build(
        str(tmp_path),
        "hello",
        [str(main)],
        False,
        False,
        "ifort",
        None,
        [],
        [],
        [],
        False,
        {"main": str(srcdir)},
        False,
    )

    text = meson_file.read_text()
    assert "link_language" not in text


@pytest.mark.base
def test_link_language_kept_for_mixed_language_target(tmp_path) -> None:
    srcdir = tmp_path / "src"
    srcdir.mkdir()
    main = srcdir / "main.f90"
    main.write_text("      program main\n      end\n")
    util = srcdir / "util.c"
    util.write_text("int util(void) { return 0; }\n")

    meson_file, _, _ = _create_main_meson_build(
        str(tmp_path),
        "hello",
        [str(main), str(util)],
        False,
        False,
        "ifort",
        "icc",
        [],
        [],
        [],
        False,
        {"main": str(srcdir)},
        False,
    )

    text = meson_file.read_text()
    assert "link_language: 'fortran'" in text


@pytest.mark.base
def test_static_intel_mixed_language_executable() -> None:
    _, flags = _get_linker_flags(
        "mixedmain",
        "ifort",
        "icc",
        [],
        ["main.f90", "util.c"],
        sharedobject=False,
        osname="linux",
    )

    assert "-Wl,-Bstatic" in flags and "-Wl,-Bdynamic" in flags
    assert (
        flags.index("-Wl,-Bstatic")
        < flags.index("-lifcore")
        < flags.index("-limf")
        < flags.index("-Wl,-Bdynamic")
    )


@pytest.mark.base
def test_static_intel_single_language_executable() -> None:
    _, flags = _get_linker_flags(
        "mp7", "ifort", None, [], ["main.f90"], sharedobject=False, osname="linux"
    )

    assert "-Wl,-Bstatic" not in flags


@pytest.mark.base
def test_static_intel_sharedobject() -> None:
    _, flags = _get_linker_flags(
        "libmf6", "ifort", None, [], ["main.f90"], sharedobject=True, osname="linux"
    )

    assert "-Wl,-Bstatic" not in flags
