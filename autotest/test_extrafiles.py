"""Tests for the extra source files a target is built with.

Cases:
  - test_fpp_replaced_by_free_format : an extra file listed with a .fpp
                                       extension is taken from the .f90 file
                                       that replaced it.
  - test_extrafile_missing           : an extra file that is not there and has
                                       not been replaced is an error.
"""

import pytest

from pymake.pymake_base import _pymake_initialize


def _initialize(tmp_path, extrafiles):
    """Initialize a build whose source is a single free format file."""
    srcdir = tmp_path / "src"
    srcdir.mkdir(parents=True)
    (srcdir / "main.f90").write_text("      program main\n      end\n")

    return _pymake_initialize(
        str(srcdir),
        str(tmp_path / "target"),
        None,
        str(extrafiles),
        None,
        False,
        str(tmp_path / "obj_temp"),
        str(tmp_path / "mod_temp"),
        str(srcdir),
    )


@pytest.mark.base
def test_fpp_replaced_by_free_format(tmp_path) -> None:
    """An extra .fpp file is taken from the .f90 file that replaced it."""
    extra = tmp_path / "extra"
    extra.mkdir(parents=True)
    (extra / "util.f90").write_text("      subroutine util\n      end\n")

    extrafiles = tmp_path / "extrafiles.txt"
    extrafiles.write_text(f"{extra / 'util.fpp'}\n")

    srcfiles = _initialize(tmp_path, extrafiles)

    assert any(pth.endswith("util.f90") for pth in srcfiles), (
        f"the free format file replacing the .fpp file is not built: {srcfiles}"
    )


@pytest.mark.base
def test_extrafile_missing(tmp_path) -> None:
    """An extra file that is not there and has no replacement is an error."""
    extrafiles = tmp_path / "extrafiles.txt"
    extrafiles.write_text(f"{tmp_path / 'gone' / 'util.fpp'}\n")

    with pytest.raises(FileNotFoundError):
        _initialize(tmp_path, extrafiles)
