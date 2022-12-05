import os
import pathlib as pl
import shutil
import subprocess
import sys

import pytest

targets = ["triangle", "crt"]

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
@pytest.mark.parametrize("target", targets)
def test_make_program(target: str) -> None:
    cmd = ["make-program", target, "--appdir", str(dstpth)]
    run_cli_cmd(cmd)


@pytest.mark.dependency(name="clean", depends=["make_program"])
@pytest.mark.base
def test_clean_up() -> None:
    # clean_up()
    return


if __name__ == "__main__":
    for target in targets:
        test_make_program(target)
    test_code_json()
    test_clean_up()
