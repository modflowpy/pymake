"""Private functions for running pymake commands using Popen"""

import sys
from subprocess import PIPE, STDOUT, Popen

PY3 = sys.version_info[0] >= 3


def _process_Popen_initialize(cmdlist, intelwin=False, cwd=None):
    """Generic function to initialize a Popen process.

    Parameters
    ----------
    cmdlist : list
        command list passed to Popen
    intelwin : bool
        boolean indicating is Intel compilers are being used on Windows and
        if stderr should be sent to the terminal
    cwd : str
        path to execute Popen in (defaulr is None)

    Returns
    -------
    proc : Popen
        Popen instance

    """
    if intelwin:
        stderr = STDOUT
    else:
        stderr = PIPE

    return Popen(cmdlist, stdout=PIPE, stderr=stderr, cwd=cwd)


def _process_Popen_command(shellflg, cmdlist):
    """Generic function to write Popen command data to the screen.

    Parameters
    ----------
    shellflg : bool
        boolean indicating if output is sent to shell by Popen
    cmdlist : list
        command list passed to Popen

    Returns
    -------
    None

    """
    if not shellflg:
        if isinstance(cmdlist, str):
            print(cmdlist)
        elif isinstance(cmdlist, list):
            print(" ".join(cmdlist))
    return


def _process_Popen_communicate(proc, verbose=True):
    """Generic function to write communication information from Popen to the
    screen.

    Parameters
    ----------
    proc : Popen
        Popen instance
    verbose : bool
        boolean indicating if stdout and stderr should be sent to terminal
        (default is True)

    Returns
    -------
    stdout : str
        proc.stdout
    stderr : str
        proc.stderr

    """
    stdout, stderr = proc.communicate()

    if stdout:
        if PY3:
            stdout = stdout.decode()
        if verbose:
            print(stdout)
    if stderr:
        if PY3:
            stderr = stderr.decode()
        if verbose:
            print(stderr)

    # catch non-zero return code
    if proc.returncode != 0:
        msg = (
            f"{' '.join(proc.args)} failed\n"
            + f"\tstatus code {proc.returncode}\n"
        )
        print(msg)

    return stderr, stdout


def _process_Popen_stdout(proc):
    """Generic function to write Popen stdout data to the terminal.

    Parameters
    ----------
    proc : Popen
        Popen instance

    Returns
    -------
    None

    """
    # write stdout to the terminal
    while True:
        line = proc.stdout.readline()
        c = line.decode("utf-8")
        if c != "":
            c = c.rstrip("\r\n")
            print(f"{c}")
        else:
            break

    # setup a communicator so that the Popen return code is set
    proc.communicate()

    return
