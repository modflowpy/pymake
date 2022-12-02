import os
import shutil
import sys

import flopy
import pytest

import pymake

# working directory
dstpth = os.path.join(f"temp_{os.path.basename(__file__).replace('.py', '')}")


@pytest.mark.dependency(name="meson")
@pytest.mark.base
def test_triangle_meson():
    os.makedirs(dstpth, exist_ok=True)

    target = "triangle"
    pm = pymake.Pymake(verbose=True)
    pm.target = target
    pm.appdir = os.path.join(dstpth, "bin")
    pm.inplace = True
    pm.meson = True
    pm.mesondir = os.path.join(dstpth)

    # download the target
    pm.download_target(target, download_path=dstpth)
    assert pm.download, f"could not download {target}"

    # build triangle
    assert pm.build() == 0, f"could not compile {target}"

    if sys.platform.lower() == "win32":
        target += ".exe"
    assert os.path.isfile(
        os.path.join(pm.appdir, target)
    ), f"could not build {target} with makefile"

    return


@pytest.mark.dependency(name="clean", depends=["meson"])
@pytest.mark.base
def test_clean_up():
    print("Removing test files and directories")

    shutil.rmtree(dstpth)


if __name__ == "__main__":
    test_triangle_meson()
    # test_clean_up()
