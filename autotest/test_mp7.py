import os
import re
import shutil
from pathlib import Path
from platform import system

import flopy
import pytest

import pymake

ext = ".exe" if system() == "Windows" else ""

TARGET_NAME = "mp7"


@pytest.fixture(scope="module")
def target(module_tmpdir):
    name = TARGET_NAME
    return module_tmpdir / f"{name}{ext}"


@pytest.fixture(scope="module")
def prog_data(target) -> dict:
    return pymake.usgs_program_data.get_target(target.name)


@pytest.fixture(scope="module")
def workspace(module_tmpdir, prog_data) -> Path:
    return module_tmpdir / prog_data.dirname


@pytest.fixture(scope="module")
def pm(module_tmpdir, target) -> pymake.Pymake:
    pm = pymake.Pymake(verbose=True)
    pm.target = str(target)
    pm.appdir = str(module_tmpdir)
    yield pm
    pm.finalize()


def replace_data(dpth):
    fpths = [
        name for name in os.listdir(dpth) if os.path.isfile(os.path.join(dpth, name))
    ]
    edits = []
    if "ex01_mf2005.dis" in fpths:
        edits.append(
            (
                "ex01_mf2005.dis",
                ["! Example 1: MODFLOW-2005 discretization file"],
                ["# Example 1: MODFLOW-2005 discretization file\n"],
            )
        )
    elif "ex04_mf6.disv" in fpths:
        edits.append(
            (
                "ex04_mf6.disv",
                ["  OPEN/CLOSE  mptest006_idomain.csv"],
                ["  OPEN/CLOSE  ex04_mf6_idomain.csv\n"],
            )
        )
        # the output control file writes mptest006_mf6.* but
        # ex04_mf6.mpnam reads ex04_mf6.bud and ex04_mf6.hed
        edits.append(
            (
                "ex04_mf6.oc",
                [
                    "  BUDGET FILEOUT mptest006_mf6.bud",
                    "  HEAD FILEOUT mptest006_mf6.hed",
                ],
                ["  BUDGET FILEOUT ex04_mf6.bud\n", "  HEAD FILEOUT ex04_mf6.hed\n"],
            )
        )
    elif "mfsim.nam" in fpths:
        edits.append(
            (
                "mfsim.nam",
                [
                    "  TDIS6  ex02a_mf6.tdis",
                    "  GWF6  ex02a_mf6.nam  ex02a_mf6",
                    "  IMS6  ex02a_mf6.ims  ex02a_mf6",
                ],
                [
                    "  TDIS6  ex02_mf6.tdis\n",
                    "  GWF6  ex02_mf6.nam  ex02_mf6\n",
                    "  IMS6  ex02_mf6.ims  ex02_mf6\n",
                ],
            )
        )
    for fname, sfinds, srepls in edits:
        fpth = os.path.join(dpth, fname)
        with open(fpth, "r") as f:
            content = f.readlines()
        for idx, line in enumerate(content):
            for jdx, sfind in enumerate(sfinds):
                if sfind in line:
                    content[idx] = srepls[jdx]
        with open(fpth, "w") as f:
            f.writelines(content)

    # MODFLOW 6.8.0 removed the IMS keywords OUTER_HCLOSE and INNER_HCLOSE,
    # which the examples still use, in favor of OUTER_DVCLOSE and INNER_DVCLOSE
    for fname in fpths:
        if not fname.lower().endswith(".ims"):
            continue
        fpth = Path(dpth) / fname
        text = fpth.read_text()
        fpth.write_text(re.sub(r"(?i)\b(outer|inner)_hclose\b", r"\1_DVCLOSE", text))


def set_lowercase(fpth):
    with open(fpth, "r") as f:
        content = f.readlines()
    for idx, line in enumerate(content):
        content[idx] = line.lower()
    with open(fpth, "w") as f:
        f.writelines(content)


def run_modpath7(namefile, mp7_exe, mf2005_exe, mfusg_exe, mf6_exe):
    model_ws = (namefile).resolve().parent
    # run the flow model
    run = True
    name = model_ws.name.lower()
    if name.endswith("_mf2005"):
        v = shutil.which(mf2005_exe)
        if v is None:
            run = False
        nam = [name for name in os.listdir(model_ws) if ".nam" in name.lower()]
        if len(nam) > 0:
            fpth = nam[0]
            # read and rewrite the name file
            set_lowercase(os.path.join(model_ws, fpth))
        else:
            fpth = None
            run = False
    elif name.endswith("_mfusg"):
        v = shutil.which(mfusg_exe)
        if v is None:
            run = False
        nam = [name for name in os.listdir(model_ws) if ".nam" in name.lower()]
        if len(nam) > 0:
            fpth = nam[0]
        else:
            fpth = None
            run = False
    elif name.endswith("_mf6"):
        v = shutil.which(mf6_exe)
        if v is None:
            run = False
        fpth = None
    else:
        run = False

    success = False

    if run:
        # fix any known problems
        replace_data(model_ws)
        # run the model
        msg = f"{mp7_exe}"
        if fpth is not None:
            msg += f" {os.path.basename(fpth)}"
        success, _ = flopy.run_model(v, fpth, model_ws=model_ws, silent=False)

    if success:
        fpth = os.path.basename(namefile)
        success, _ = flopy.run_model(mp7_exe, fpth, model_ws=model_ws, silent=False)

    return success


@pytest.mark.dependency(name="download")
@pytest.mark.xdist_group(TARGET_NAME)
@pytest.mark.regression
def test_download(pm, module_tmpdir, target):
    pm.download_target(target, download_path=module_tmpdir)
    assert pm.download, f"could not download {target} distribution"


@pytest.mark.dependency(name="build", depends=["download"])
@pytest.mark.xdist_group(TARGET_NAME)
@pytest.mark.regression
def test_compile(pm, target):
    assert pm.build() == 0, f"could not compile {target}"


@pytest.mark.dependency(depends=["build"])
@pytest.mark.xdist_group(TARGET_NAME)
@pytest.mark.regression
def test_static_intel(pm, target, check_static_intel):
    # a fortran-only target
    check_static_intel(target, pm.fc)


@pytest.mark.dependency(name="download_exes")
@pytest.mark.xdist_group(TARGET_NAME)
@pytest.mark.regression
def test_download_exes(module_tmpdir):
    pymake.getmfexes(str(module_tmpdir), exes=("mf2005", "mfusg", "mf6"), verbose=True)


@pytest.mark.dependency(name="test", depends=["download", "download_exes", "build"])
@pytest.mark.xdist_group(TARGET_NAME)
@pytest.mark.regression
@pytest.mark.parametrize(
    "namefile",
    [
        "ex01_mf2005/ex01a_mf2005.mpsim",
        "ex01_mf2005/ex01b_mf2005.mpsim",
        "ex01_mf6/ex01a_mf6.mpsim",
        "ex01_mf6/ex01b_mf6.mpsim",
        "ex02_mf6/ex02a_mf6.mpsim",
        "ex02_mf6/ex02b_mf6.mpsim",
        "ex02_mfusg/ex02a_mfusg.mpsim",
        "ex02_mfusg/ex02b_mfusg.mpsim",
        "ex03_mf6/ex03a_mf6.mpsim",
        "ex04_mf6/ex04a_mf6.mpsim",
    ],
)
def test_modpath7(module_tmpdir, namefile, workspace, target):
    assert run_modpath7(
        workspace / "examples" / namefile,
        target,
        module_tmpdir / f"mf2005{ext}",
        module_tmpdir / f"mfusg{ext}",
        module_tmpdir / f"mf6{ext}",
    ), f"could not run {namefile}"
