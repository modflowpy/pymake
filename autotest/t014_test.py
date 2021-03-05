import os
import sys
import shutil
import pymake

import pytest

# define program data
targets = [
    "crt",
    "vs2dt",
    "zonbud3",
]

app_extension = ""
if sys.platform.lower() == "win32":
    app_extension = ".exe"

for idx, target in enumerate(targets):
    target_dict = pymake.usgs_program_data.get_target(target)
    if target_dict.shared_object:
        extension = shared_extension
    else:
        extension = app_extension
    targets[idx] = target + extension

# set up paths
dstpth = os.path.join("temp", "t014")
if not os.path.exists(dstpth):
    os.makedirs(dstpth)

appdir = os.path.join(dstpth, "bin")
if not os.path.exists(appdir):
    os.makedirs(appdir)

exe_names = [os.path.join(appdir, target) for target in targets]


def clean_up(epth):
    assert os.path.isfile(epth), "{} does not exist".format(
        os.path.basename(epth)
    )
    print("Removing " + os.path.basename(epth))
    os.remove(epth)


@pytest.mark.base
@pytest.mark.regression
@pytest.mark.parametrize("target", targets)
def test_compile(target):
    assert (
        pymake.build_apps(
            target, download_dir=dstpth, appdir=appdir, verbose=True
        )
        == 0
    ), "could not compile {}".format(target)


@pytest.mark.base
@pytest.mark.regression
@pytest.mark.parametrize("epth", exe_names)
def test_clean_up(epth):
    clean_up(epth)


def test_finalize():
    shutil.rmtree(dstpth)


if __name__ == "__main__":
    for target in targets:
        test_compile(target)
    for exe_name in exe_names:
        test_clean_up(exe_name)
    test_finalize()
