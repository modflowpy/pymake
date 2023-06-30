import os
import pathlib as pl
import shutil
import subprocess

import pytest
from flaky import flaky

RERUNS = 3

targets = (
    "triangle",
    "crt",
    "mf6dev",
)


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


@pytest.mark.dependency(name="make_program")
@pytest.mark.base
@flaky(max_runs=RERUNS)
@pytest.mark.parametrize("target", targets)
def test_make_program(function_tmpdir, target: str) -> None:
    os.chdir(function_tmpdir)
    cmd = ["make-program", target, "--appdir", ".", "--verbose", "--mg"]
    run_cli_cmd(cmd)


@pytest.mark.dependency(name="make_program_all")
@flaky(max_runs=RERUNS)
@pytest.mark.schedule
def test_make_program_all(function_tmpdir) -> None:
    os.chdir(function_tmpdir)
    cmd = [
        "make-program",
        ":",
        "--appdir",
        ".",
        "--verbose",
        "--dryrun",
    ]
    run_cli_cmd(cmd)


@pytest.mark.dependency(name="mfpymake")
@pytest.mark.base
def test_mfpymake(function_tmpdir) -> None:
    src = (
        "program hello\n"
        + "  ! This is a comment line; it is ignored by the compiler\n"
        + "  print *, 'Hello, World!'\n"
        + "end program hello\n"
    )
    src_file = function_tmpdir / "mfpymake_src/hello.f90"
    src_file.parent.mkdir(parents=True, exist_ok=True)
    with open(src_file, "w") as f:
        f.write(src)
    cmd = [
        "mfpymake",
        str(src_file.parent),
        "hello",
        "-mc",
        "--verbose",
        "--appdir",
        str(function_tmpdir),
        "-fc",
    ]
    if os.environ.get("FC") is None:
        cmd.append("gfortran")
    else:
        cmd.append(os.environ.get("FC"))
    run_cli_cmd(cmd)
    cmd = [str(function_tmpdir) / "hello"]
    run_cli_cmd(cmd)
