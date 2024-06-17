from pathlib import Path

import pytest

import pymake


@pytest.fixture(scope="module")
def target(module_tmpdir) -> Path:
    target = "mflgr"
    return module_tmpdir / target


@pytest.fixture(scope="module")
def prog_dict(target) -> dict:
    return pymake.usgs_program_data.get_target(target)


@pytest.fixture(scope="module")
def workspace(module_tmpdir, prog_dict) -> Path:
    return module_tmpdir / prog_dict.dirname


def compile_code(ws, exe):
    return pymake.build_apps(
        str(exe), download_dir=ws, appdir=ws, verbose=True
    )


@pytest.mark.base
def test_compile(module_tmpdir, target):
    assert (
        compile_code(module_tmpdir, target) == 0
    ), f"could not compile {target}"
