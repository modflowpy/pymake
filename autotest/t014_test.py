import platform

import pytest

import pymake

_system = platform.system()
_eext = "" if _system != "Windows" else ".exe"
_lext = ".so" if _system == "Linux" else ".dylib" if _system == "Darwin" else ".dll"

_targets = [
    "crt",
    "vs2dt",
    "zonbud3",
]

for idx, target in enumerate(_targets):
    target_dict = pymake.usgs_program_data.get_target(target)
    _targets[idx] = target + (_lext if target_dict.shared_object else _eext)


@pytest.mark.base
@pytest.mark.regression
@pytest.mark.parametrize("target", _targets)
def test_compile(target, tmp_path):
    dl_dir = tmp_path / "dl"
    bin_dir = tmp_path / "bin"
    assert (
        pymake.build_apps(
            target, download_dir=str(dl_dir), appdir=str(bin_dir), verbose=True
        )
        == 0
    ), f"could not compile {target}"
