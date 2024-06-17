import pytest

import pymake

targets = [
    "crt",
    "vs2dt",
    "zonbud3",
]


@pytest.mark.base
@pytest.mark.parametrize("target", targets)
def test_compile(module_tmpdir, target):
    bin_dir = module_tmpdir / "bin"
    assert (
        pymake.build_apps(
            str(bin_dir / target),
            download_dir=str(module_tmpdir),
            appdir=str(bin_dir),
            verbose=True,
        )
        == 0
    ), f"could not compile {target}"
