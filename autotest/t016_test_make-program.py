import os
import pathlib as pl
import shutil
import subprocess

import pytest

targets = ["triangle", "crt"]

# set up paths
dstpth = pl.Path(
    f"temp_{os.path.basename(__file__).replace('.py', '')}"
).resolve()
dstpth.mkdir(parents=True, exist_ok=True)


def make_program(cmd):
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
    return process.returncode


def clean_up():
    print("Removing temporary build directories")
    dirs_temp = [dstpth]
    for d in dirs_temp:
        if os.path.isdir(d):
            shutil.rmtree(d)
    return


@pytest.mark.regression
@pytest.mark.parametrize("target", targets)
def test_make_program(target):
    cmd = ["make-program", "--targets", target, "--appdir", dstpth]
    rc = make_program(cmd)
    assert rc == 0, f"'{' '.join(cmd)}' failed\n\tstatus code {rc}\n"


@pytest.mark.base
@pytest.mark.regression
def test_clean_up():
    clean_up()
    return


if __name__ == "__main__":
    for target in targets:
        test_make_program(target)
    test_clean_up()
