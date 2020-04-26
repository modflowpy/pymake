# Test the download_and_unzip functionality of pymake

import os
import shutil
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


def test_latest_version():
    mfexes_repo_name = 'MODFLOW-USGS/executables'
    version = pymake.repo_latest_version(mfexes_repo_name)
    test_version = '3.0'
    msg = 'returned version ({}) '.format(version) + \
          'is not equal to defined version ({})'.format(test_version)
    assert version == test_version, msg
    return


def test_assets():
    mfexes_repo_name = 'MODFLOW-USGS/executables'
    assets = pymake.repo_latest_assets(mfexes_repo_name)
    keys = assets.keys()
    test_keys = ['mac.zip', 'linux.zip', 'win32.zip', 'win64.zip']
    for key in keys:
        msg = 'unknown key ({}) found in github repo assets'.format(key)
        assert key in test_keys, msg
    return


def test_download_and_unzip():
    pth = './temp/t999'
    pymake.getmfexes(pth, '3.0')
    for f in os.listdir(pth):
        fpth = os.path.join(pth, f)
        if not os.path.isdir(fpth):
            errmsg = '{} not executable'.format(fpth)
            assert which(fpth) is not None, errmsg

    # clean up exe's
    for f in os.listdir(pth):
        fpth = os.path.join(pth, f)
        if not os.path.isdir(fpth):
            print('Removing ' + f)
            os.remove(fpth)

    # clean up directory
    if os.path.isdir(pth):
        print('Removing folder ' + pth)
        shutil.rmtree(pth)

    return


if __name__ == '__main__':
    test_latest_version()
    test_assets()
    test_download_and_unzip()
