"""Tests for statically linking the intel fortran runtime by default.

ifort/mpiifort targets on osx/linux get -static-intel unconditionally,
exe or shared alike: ifort honors the last of a repeated
static-intel/shared-intel, and a caller's syslibs land after ours, so
-shared-intel overrides it with no special-casing needed.

Verified against a real ifort 2021.7.1 build: pure-fortran exe/shared
objects came out static by default and switched to dynamic with
-shared-intel. A fortran+c exe stayed static regardless (the bracket
below) -- a known, narrow gap.
"""

import pytest

from pymake import Pymake
from pymake.utils._compiler_switches import _get_linker_flags
from pymake.utils._meson_build import _create_main_meson_build


@pytest.mark.base
@pytest.mark.parametrize("osname", ["linux", "darwin"])
def test_static_intel_default_for_executable(osname) -> None:
    """An ifort executable gets -static-intel by default on osx and linux."""
    _, flags = _get_linker_flags(
        "mp7", "ifort", None, [], ["main.f90"], sharedobject=False, osname=osname
    )

    assert "-static-intel" in flags, (
        f"an ifort executable is not statically linked by default: {flags}"
    )


@pytest.mark.base
def test_static_intel_default_for_sharedobject() -> None:
    """An ifort shared object gets -static-intel too."""
    _, flags = _get_linker_flags(
        "libmf6", "ifort", None, [], ["main.f90"], sharedobject=True, osname="linux"
    )

    assert "-static-intel" in flags, (
        f"an ifort shared object is not statically linked by default: {flags}"
    )


@pytest.mark.base
def test_shared_intel_overrides_static_intel_default() -> None:
    """A caller's -shared-intel is appended after the default and wins."""
    _, flags = _get_linker_flags(
        "mp7",
        "ifort",
        None,
        ["-shared-intel"],
        ["main.f90"],
        sharedobject=False,
        osname="linux",
    )

    assert "-static-intel" in flags and "-shared-intel" in flags, (
        f"one of the two static/shared-intel flags is missing: {flags}"
    )
    assert flags.index("-static-intel") < flags.index("-shared-intel"), (
        f"-shared-intel does not come after the default -static-intel, so "
        f"ifort would not honor it as the later, overriding flag: {flags}"
    )


@pytest.mark.base
def test_gfortran_unaffected() -> None:
    """A gfortran target is not given -static-intel."""
    _, flags = _get_linker_flags(
        "mp7", "gfortran", None, [], ["main.f90"], sharedobject=False, osname="linux"
    )

    assert "-static-intel" not in flags, (
        f"-static-intel was added for a non-intel compiler: {flags}"
    )


@pytest.mark.base
def test_static_intel_kept_for_executable() -> None:
    """Pymake no longer strips -static-intel from a non-shared target."""
    pm = Pymake()
    pm.target = "mp7"
    pm.syslibs = "-static-intel"

    pm._set_sharedobject()

    assert pm.sharedobject is False
    assert pm.syslibs == "-static-intel", (
        f"-static-intel was stripped from an executable's syslibs: {pm.syslibs!r}"
    )


@pytest.mark.base
def test_link_language_omitted_for_single_language_target(tmp_path) -> None:
    """link_language is not set for a single-source-language target."""
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
    assert "link_language" not in text, (
        f"link_language was set for a single-language target: {text}"
    )


@pytest.mark.base
def test_link_language_kept_for_mixed_language_target(tmp_path) -> None:
    """link_language is kept for a target that mixes fortran and c."""
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
    assert "link_language: 'fortran'" in text, (
        f"link_language was dropped for a mixed-language target: {text}"
    )


@pytest.mark.base
def test_static_intel_bracket_for_mixed_language_executable() -> None:
    """A non-shared, mixed-language ifort/linux target gets the bracket."""
    _, flags = _get_linker_flags(
        "mixedmain",
        "ifort",
        "icc",
        [],
        ["main.f90", "util.c"],
        sharedobject=False,
        osname="linux",
    )

    assert "-Wl,-Bstatic" in flags and "-Wl,-Bdynamic" in flags, (
        f"the static bracket is missing: {flags}"
    )
    assert (
        flags.index("-Wl,-Bstatic")
        < flags.index("-lifcore")
        < flags.index("-limf")
        < flags.index("-Wl,-Bdynamic")
    ), f"the static bracket is out of order: {flags}"


@pytest.mark.base
def test_static_intel_bracket_skipped_for_single_language_executable() -> None:
    """A single-language executable does not get the static bracket."""
    _, flags = _get_linker_flags(
        "mp7", "ifort", None, [], ["main.f90"], sharedobject=False, osname="linux"
    )

    assert "-Wl,-Bstatic" not in flags, (
        f"the static bracket was added to a single-language executable: {flags}"
    )


@pytest.mark.base
def test_static_intel_bracket_skipped_for_sharedobject() -> None:
    """A shared object skips the bracket: libifcore.a isn't -fPIC."""
    _, flags = _get_linker_flags(
        "libmf6", "ifort", None, [], ["main.f90"], sharedobject=True, osname="linux"
    )

    assert "-Wl,-Bstatic" not in flags, (
        f"the static bracket was added to a shared object: {flags}"
    )
