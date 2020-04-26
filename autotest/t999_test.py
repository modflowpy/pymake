# Test the download_and_unzip functionality of pymake

import sys
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


def repo_latest_assets(github_repo):
    """
    Return a dictionary containing the file name and the link to the asset
    contained in a github repository.

    Parameters
    ----------
    github_repo : str
        Repository name, such as MODFLOW-USGS/modflow6

    Returns
    -------
    result_dict : dict
        dictionary of file names and links

    """
    import requests
    import json
    repo_url = 'https://api.github.com/repos/{}'.format(github_repo)

    assets = None
    request_url = '{}/releases/latest'.format(repo_url)
    print('Requesting from: {}'.format(request_url))
    r = requests.get(request_url)
    if (r.ok):
        jsonobj = json.loads(r.text or r.content)
        assets = jsonobj['assets']
    else:
        assert assets, 'Could not find latest executables from ' + request_url

    result_dict = {}
    for asset in assets:
        k = asset['name']
        v = asset['browser_download_url']
        result_dict[k] = v
    return result_dict


def test_download_and_unzip():
    pth = './temp/t999'
    pymake.getmfexes(pth, '3.0')
    for f in os.listdir(pth):
        fname = os.path.join(pth, f)
        errmsg = '{} not executable'.format(fname)
        assert which(fname) is not None, errmsg

    # clean up exe's
    for f in os.listdir(pth):
        fpth = os.path.join(pth, f)
        print('Removing ' + f)
        os.remove(fpth)

    # clean up directory
    if os.path.isdir(pth):
        print('Removing folder ' + pth)
        shutil.rmtree(pth)

    return


if __name__ == '__main__':
    test_download_and_unzip()
