"""Tests for the user flags a generated makefile is written with.

The flag has to be set on the makefile variable it belongs to, because the
c flags were previously written from the fortran flags, which put a fortran
flag in the makefile without it being the flag the c compiler is given.

Cases:
  - test_fflags_in_fflags   : a fortran flag that was asked for is set on FFLAGS.
  - test_cflags_in_cflags   : a c flag that was asked for is set on CFLAGS.
  - test_syslibs_in_ldflags : a linker flag that was asked for is set on LDFLAGS.
  - test_flags_kept_apart   : a flag is set only on the variable it belongs to.
"""

import pytest

from pymake.pymake_base import _create_makefile

FFLAG = "-DPYMAKE_TEST_FFLAG"
CFLAG = "-DPYMAKE_TEST_CFLAG"
SYSLIB = "-lpymaketestlib"


def _makedefaults(tmp_path, fflags, cflags, syslibs):
    """Write a makefile for a target with one fortran and one c source file."""
    srcdir = tmp_path / "src"
    srcdir.mkdir(parents=True)
    main = srcdir / "main.f90"
    main.write_text("      program main\n      end\n")
    util = srcdir / "util.c"
    util.write_text("int util(void) { return 0; }\n")

    _create_makefile(
        str(tmp_path / "target"),
        str(srcdir),
        None,
        None,
        [str(main), str(util)],
        False,
        False,
        "gfortran",
        "gcc",
        fflags,
        cflags,
        syslibs,
        False,
        str(tmp_path),
        False,
    )

    return (tmp_path / "makedefaults").read_text()


def _flags(text, variable):
    """Get the flags every line setting a makefile variable is given."""
    flags = []
    for line in text.splitlines():
        name, _, value = line.strip().partition("?=")
        if name.strip() == variable:
            flags += value.split()

    return flags


@pytest.mark.base
def test_fflags_in_fflags(tmp_path) -> None:
    """A fortran flag that was asked for is set on FFLAGS."""
    flags = _flags(_makedefaults(tmp_path, [FFLAG], [], []), "FFLAGS")

    assert FFLAG in flags, f"the fortran flag is not set on FFLAGS: {flags}"


@pytest.mark.base
def test_cflags_in_cflags(tmp_path) -> None:
    """A c flag that was asked for is set on CFLAGS."""
    flags = _flags(_makedefaults(tmp_path, [], [CFLAG], []), "CFLAGS")

    assert CFLAG in flags, f"the c flag is not set on CFLAGS: {flags}"


@pytest.mark.base
def test_syslibs_in_ldflags(tmp_path) -> None:
    """A linker flag that was asked for is set on LDFLAGS."""
    flags = _flags(_makedefaults(tmp_path, [], [], [SYSLIB]), "LDFLAGS")

    assert SYSLIB in flags, f"the linker flag is not set on LDFLAGS: {flags}"


@pytest.mark.base
def test_flags_kept_apart(tmp_path) -> None:
    """A flag is set only on the makefile variable it belongs to."""
    text = _makedefaults(tmp_path, [FFLAG], [CFLAG], [SYSLIB])

    assert FFLAG not in _flags(text, "CFLAGS"), "the fortran flag is set on CFLAGS"
    assert CFLAG not in _flags(text, "FFLAGS"), "the c flag is set on FFLAGS"
