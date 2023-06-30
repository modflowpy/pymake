import pytest

import pymake

targets = [
    "crt",
    "vs2dt",
    "zonbud3",
]


@pytest.mark.base
@pytest.mark.parametrize("target", targets)
def test_compile(function_tmpdir, target):
    dstpth = str(function_tmpdir)
    appdir = function_tmpdir / "bin"
    assert (
        pymake.build_apps(
            target, download_dir=dstpth, appdir=appdir, verbose=True
        )
        == 0
    ), f"could not compile {target}"
