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


def getmfexes(pth='.', version='', platform=None):
    """
    Get the latest MODFLOW binary executables from a github site
    (https://github.com/MODFLOW-USGS/executables) for the specified
    operating system and put them in the specified path.

    Parameters
    ----------
    pth : str
        Location to put the executables (default is current working directory)

    version : str
        Version of the MODFLOW-USGS/executables release to use.

    platform : str
        Platform that will run the executables.  Valid values include mac,
        linux, win32 and win64.  If platform is None, then routine will
        download the latest asset from the github reposity.

    """

    # Determine the platform in order to construct the zip file name
    if platform is None:
        if sys.platform.lower() == 'darwin':
            platform = 'mac'
        elif sys.platform.lower().startswith('linux'):
            platform = 'linux'
        elif 'win' in sys.platform.lower():
            is_64bits = sys.maxsize > 2 ** 32
            if is_64bits:
                platform = 'win64'
            else:
                platform = 'win32'
        else:
            errmsg = ('Could not determine platform'
                      '.  sys.platform is {}'.format(sys.platform))
            raise Exception(errmsg)
    else:
        assert platform in ['mac', 'linux', 'win32', 'win64']
    zipname = '{}.zip'.format(platform)

    # Wanted to use github api, but this is timing out on travis too often
    #mfexes_repo_name = 'MODFLOW-USGS/executables'
    # assets = repo_latest_assets(mfexes_repo_name)

    # Determine path for file download and then download and unzip
    url = ('https://github.com/MODFLOW-USGS/executables/'
           'releases/download/{}/'.format(version))
    assets = {p: url + p for p in ['mac.zip', 'linux.zip',
                                   'win32.zip', 'win64.zip']}
    download_url = assets[zipname]
    pymake.download_and_unzip(download_url, pth)

    return


def test_download_and_unzip():
    pth = './temp/t009'
    getmfexes(pth, '1.0')
    for f in os.listdir(pth):
        fname = os.path.join(pth, f)
        errmsg = '{} not executable'.format(fname)
        assert which(fname) is not None, errmsg
    return

if __name__ == '__main__':
    test_download_and_unzip()
