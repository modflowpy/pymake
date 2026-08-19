"""Tests for the meson build files pymake generates.

Cases:
  - test_include_dirs_found  : every directory that holds a header file is an
                               include directory, and one that holds no header
                               file is not.
  - test_include_dirs_sorted : the include directories are in the same order
                               whatever order the file system returns them in,
                               so a generated meson.build can be reproduced.
"""

import pytest

from pymake.utils._meson_build import _get_include_dirs

# names that are not in alphabetical order, so an order the file system
# returns can be told apart from a sorted one
_HEADER_DIRS = ("tools", "basic", "vpass", "grid", "intersection", "shapelib")


@pytest.fixture
def srcdir(tmp_path):
    """A source tree with a header in each of several directories."""
    for name in _HEADER_DIRS:
        pth = tmp_path / "src" / name
        pth.mkdir(parents=True)
        (pth / f"{name}.h").write_text(f"/* {name} */\n")

    # a directory with a source file but no header is not an include directory
    nohdr = tmp_path / "src" / "nohdr"
    nohdr.mkdir(parents=True)
    (nohdr / "nohdr.c").write_text("int main() { return 0; }\n")

    return tmp_path


@pytest.mark.base
def test_include_dirs_found(srcdir) -> None:
    """A directory is an include directory when it holds a header file."""
    include_dirs = _get_include_dirs({"main": srcdir / "src"}, srcdir)

    assert sorted(include_dirs) == sorted(f"src/{name}" for name in _HEADER_DIRS), (
        f"the include directories are not the ones with a header: {include_dirs}"
    )


@pytest.mark.base
def test_include_dirs_sorted(srcdir) -> None:
    """The include directories are sorted.

    The directories are found by walking the source tree, which is read in the
    order the file system returns, so an unsorted order differs from one
    operating system to another and the generated meson.build file cannot be
    reproduced.
    """
    include_dirs = _get_include_dirs({"main": srcdir / "src"}, srcdir)

    assert include_dirs == sorted(include_dirs), (
        f"the include directories are not sorted: {include_dirs}"
    )
