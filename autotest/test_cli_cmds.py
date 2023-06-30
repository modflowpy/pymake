import os
import pathlib as pl
import shutil
import subprocess
import sys

import pytest
from flaky import flaky

RERUNS = 3

targets = (
    "triangle",
    "crt",
    "mf6dev",
)

# set up paths
dstpth = pl.Path(
    f"temp_{os.path.basename(__file__).replace('.py', '')}"
).resolve()
dstpth.mkdir(parents=True, exist_ok=True)


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


def clean_up() -> None:
    print("Removing temporary build directories")
    dirs_temp = [dstpth]
    for d in dirs_temp:
        if os.path.isdir(d):
            shutil.rmtree(d)
    return


@pytest.mark.dependency(name="make_program")
@pytest.mark.base
@flaky(max_runs=RERUNS)
@pytest.mark.parametrize("target", targets)
def test_make_program(target: str) -> None:
    cmd = [
        "make-program",
        target,
        "--appdir",
        str(dstpth),
        "--verbose",
    ]
    if sys.platform != "win32":
        cmd.append("--meson-build")
    run_cli_cmd(cmd)


@pytest.mark.dependency(name="make_program_all")
@flaky(max_runs=RERUNS)
@pytest.mark.schedule
def test_make_program_all() -> None:
    cmd = [
        "make-program",
        ":",
        "--appdir",
        str(dstpth / "all"),
        "--verbose",
        "--dryrun",
    ]
    run_cli_cmd(cmd)


@pytest.mark.dependency(name="mfpymake")
@pytest.mark.base
def test_mfpymake() -> None:
    src = (
        "program hello\n"
        + "  ! This is a comment line; it is ignored by the compiler\n"
        + "  print *, 'Hello, World!'\n"
        + "end program hello\n"
    )
    src_file = dstpth / "mfpymake_src/hello.f90"
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
        str(dstpth),
        "-fc",
    ]
    if os.environ.get("FC") is None:
        cmd.append("gfortran")
    else:
        cmd.append(os.environ.get("FC"))
    run_cli_cmd(cmd)
    cmd = [dstpth / "hello"]
    run_cli_cmd(cmd)


@pytest.mark.dependency(name="clean", depends=["make_program"])
@pytest.mark.base
def test_clean_up() -> None:
    clean_up()
    return


if __name__ == "__main__":
    for target in targets:
        test_make_program(target)
    test_clean_up()
