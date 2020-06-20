import sys
from subprocess import Popen, PIPE

PY3 = sys.version_info[0] >= 3


def process_Popen_initialize(cmdlist):
    """
    Generic function to initialize a Popen process

    Parameters
    ----------
    cmdlist : list
        command list passed to Popen

    Returns
    -------
    proc : Popen
        Popen instance

    """
    return Popen(cmdlist, stdout=PIPE, stderr=PIPE, shell=False)


def process_Popen_command(shellflg, cmdlist):
    """
    Generic function to write Popen command data to the screen.

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
            print(' '.join(cmdlist))
    return


def process_Popen_communicate(proc):
    """
    Generic function to write communication information from Popen to the
    screen.

    Parameters
    ----------
    proc : Popen
        Popen instance

    Returns
    -------
    None

    """
    stdout, stderr = proc.communicate()

    if stdout:
        if PY3:
            stdout = stdout.decode()
        print(stdout)
    if stderr:
        if PY3:
            stderr = stderr.decode()
        print(stderr)

    # catch non-zero return code
    if proc.returncode != 0:
        msg = '{} failed\n'.format(' '.join(proc.args)) + \
              '\tstatus code {}\n'.format(proc.returncode)
        print(msg)

    return


def process_Popen_stdout(proc):
    """
    Generic function to write Popen stdout data to the terminal.

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
        c = line.decode('utf-8')
        if c != '':
            c = c.rstrip('\r\n')
            print('{}'.format(c))
        else:
            break

    # setup a communicator so that the Popen return code is set
    proc.communicate()

    return
