import os
import pathlib as pl
import subprocess
from platform import system

import pytest
from flaky import flaky
from modflow_devtools.misc import set_dir

import pymake

RERUNS = 3

TARGETS = (
    "triangle",
    "crt",
)

MESON_PARM = (
    True,
    False,
)

TARGETS_ALL = pymake.usgs_program_data.get_keys(current=True)


def run_cli_cmd(cmd: list) -> None:
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.getcwd()
    )
    stdout, stderr = process.communicate()

    if stdout:
        stdout = stdout.decode()
        print(stdout)
    if stderr:
        stderr = stderr.decode()
        print(stderr)

    assert (
        process.returncode == 0
    ), f"'{' '.join(cmd)}' failed\n\tstatus code {process.returncode}\n"
    return


@flaky(max_runs=RERUNS)
@pytest.mark.dependency(name="make_program")
@pytest.mark.base
@pytest.mark.parametrize("target", TARGETS)
def test_make_program(function_tmpdir, target: str) -> None:
    with set_dir(function_tmpdir):
        cmd = [
            "make-program",
            target,
            "--appdir",
            str(function_tmpdir),
            "--verbose",
        ]
        run_cli_cmd(cmd)


@flaky(max_runs=RERUNS)
@pytest.mark.dependency(name="make_program_mf2005")
@pytest.mark.base
def test_make_program_double(function_tmpdir) -> None:
    with set_dir(function_tmpdir):
        cmd = [
            "make-program",
            "mf2005",
            "--double",
            "--verbose",
            "--appdir",
            str(function_tmpdir),
        ]
        run_cli_cmd(cmd)


@pytest.mark.dependency(name="make_program_all")
@pytest.mark.schedule
def test_make_program_all(function_tmpdir) -> None:
    with set_dir(function_tmpdir):
        cmd = [
            "make-program",
            ":",
            "--appdir",
            str(function_tmpdir),
            "--verbose",
        ]
        run_cli_cmd(cmd)


@pytest.mark.dependency(name="make_program_all_parametrize")
@pytest.mark.schedule
@pytest.mark.parametrize("target", TARGETS_ALL)
def test_make_program_all_parametrize(function_tmpdir, target: str) -> None:
    with set_dir(function_tmpdir):
        cmd = [
            "make-program",
            target,
            "--appdir",
            str(function_tmpdir),
            "--verbose",
        ]
        run_cli_cmd(cmd)


@flaky(max_runs=RERUNS)
@pytest.mark.dependency(name="mfpymake")
@pytest.mark.base
@pytest.mark.parametrize("meson", MESON_PARM)
def test_mfpymake(function_tmpdir, meson: bool) -> None:
    with set_dir(function_tmpdir):
        src = (
            "program hello\n"
            + "  ! This is a comment line; it is ignored by the compiler\n"
            + "  print *, 'Hello, World!'\n"
            + "end program hello\n"
        )
        src_file = pl.Path("src/hello.f90")
        src_file.parent.mkdir(parents=True, exist_ok=True)
        with open(src_file, "w") as f:
            f.write(src)
        cmd = [
            "mfpymake",
            str(src_file.parent),
            "hello",
            # "-mc",
            "--verbose",
            "-fc",
        ]
        fc = "gfortran"
        if os.environ.get("FC") is None:
            cmd.append(fc)
        else:
            fc = os.environ.get("FC")
            cmd.append(fc)

        pymake.linker_update_environment(fc=fc)

        if meson:
            cmd.append("--meson")
        run_cli_cmd(cmd)
        cmd = [function_tmpdir / "hello"]
        run_cli_cmd(cmd)
