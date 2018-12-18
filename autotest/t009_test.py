# Test the download_and_unzip functionality of pymake

import sys
import os
import pymake


def which(program):
    """
    Test to make sure that the program is executable

    """
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def getmfexes(pth='.'):
    """
    Download a zip file of MODFLOW executables from github and extract the
    executables into a user bin folder, which is under the user name, followed
    by .local and bin.

    """
    downloadurl = ('https://github.com/MODFLOW-USGS/executables'
                   '/releases/download/1.0')
    zipname = None
    if sys.platform.lower() == 'darwin':
        zipname = 'mac'
    elif sys.platform.lower().startswith('linux'):
        zipname = 'linux'
    elif 'win' in sys.platform.lower():
        is_64bits = sys.maxsize > 2 ** 32
        if is_64bits:
            zipname = 'win64'
        else:
            zipname = 'win32'
    else:
        errmsg = 'Could not determine platform.  sys.platform is {}'.format(sys.platform)
        raise Exception(errmsg)
    downloadurl = '{}/{}.zip'.format(downloadurl, zipname)
    pymake.download_and_unzip(downloadurl, pth)
    return


def test_download_and_unzip():
    pth = './temp/t009'
    getmfexes(pth)
    for f in os.listdir(pth):
        fname = os.path.join(pth, f)
        errmsg = '{} not executable'.format(fname)
        assert which(fname) is not None, errmsg
    return

if __name__ == '__main__':
    test_download_and_unzip()
