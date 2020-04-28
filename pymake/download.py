from __future__ import print_function

import os
import sys
import shutil
import timeit
from zipfile import ZipFile, ZipInfo
import tarfile


class MyZipFile(ZipFile):
    """
    ZipFile file attributes are not being preserved.  This preserves file
    attributes as described here
    https://stackoverflow.com/questions/39296101/python-zipfile-removes-execute-permissions-from-binaries

    """

    def extract(self, member, path=None, pwd=None):
        if not isinstance(member, ZipInfo):
            member = self.getinfo(member)

        if path is None:
            path = os.getcwd()

        ret_val = self._extract_member(member, path, pwd)
        attr = member.external_attr >> 16
        if attr != 0:
            os.chmod(ret_val, attr)
        return ret_val

    def extractall(self, path=None, members=None, pwd=None):
        if members is None:
            members = self.namelist()

        if path is None:
            path = os.getcwd()
        else:
            if hasattr(os, 'fspath'):
                # introduced in python 3.6 and above
                path = os.fspath(path)

        for zipinfo in members:
            self.extract(zipinfo, path, pwd)


def download_and_unzip(url, pth='./', delete_zip=True, verify=True,
                       timeout=30, nattempts=10, chunk_size=2048000):
    try:
        import requests
    except Exception as e:
        msg = "pymake.download_and_unzip() error import requests: " + \
              str(e)
        raise Exception(msg)
    if not os.path.exists(pth):
        print('Creating the directory:\n    {}'.format(pth))
        os.makedirs(pth)

    print('Attempting to download the file:\n    {}'.format(url))
    file_name = os.path.join(pth, url.split('/')[-1])

    # download the file
    success = False
    tic = timeit.default_timer()
    for idx in range(nattempts):
        print(' download attempt: {}'.format(idx + 1))

        # open request
        try:
            req = requests.get(url, stream=True, verify=verify)
        except TimeoutError:
            continue
        except requests.ConnectionError:
            continue
        except:
            e = sys.exc_info()[0]
            raise Exception(e)

        # connection established - download the file
        fs = 0
        lenfs = 0
        if 'Content-length' in req.headers:
            fs = req.headers['Content-length']
            lenfs = len(fs)
            fs = int(fs)
        if fs > 0:
            bfmt = '{:' + '{}'.format(lenfs) + ',d}'
            sbfmt = '{:>' + '{}'.format(len(bfmt.format(int(fs)))) + 's} bytes'
            msg = '   file size: {}'.format(sbfmt.format(bfmt.format(int(fs))))
            print(msg)
        ds = 0
        try:
            req = requests.get(url, verify=verify, timeout=timeout,
                               stream=True)
            with open(file_name, 'wb') as f:
                for chunk in req.iter_content(chunk_size=chunk_size):
                    if chunk:
                        ds += len(chunk)
                        msg = '     downloaded ' + \
                              sbfmt.format(bfmt.format(ds)) + \
                              ' of ' + bfmt.format(int(fs)) + ' bytes' + \
                              ' ({:10.4%})'.format(float(ds) / float(fs))
                        print(msg)
                        f.write(chunk)
            success = True
        except:
            if idx + 1 == nattempts:
                msg = 'Cannot download file:\n    {}'.format(url)
                raise Exception(msg)
        if success:
            break

    # write the total download time
    toc = timeit.default_timer()
    tsec = toc - tic
    print('\ntotal download time: {} seconds'.format(tsec))
    if fs > 0:
        print('download speed:      {} MB/s'.format(fs / (1e6 * tsec)))

    # Unzip the file, and delete zip file if successful.
    if 'zip' in os.path.basename(file_name) or \
            'exe' in os.path.basename(file_name):
        z = MyZipFile(file_name)
        try:
            print('Extracting the zipfile...')
            z.extractall(pth)
        except:
            p = 'Could not unzip the file.  Stopping.'
            raise Exception(p)
        z.close()
    elif 'tar' in os.path.basename(file_name):
        ar = tarfile.open(file_name)
        ar.extractall(path=pth)
        ar.close()

    # delete the zipfile
    if delete_zip:
        print('Deleting the zipfile...')
        os.remove(file_name)
    print('Done downloading and extracting...\n')


def get_default_repo():
    """
    Return the default repo name

    Returns
    -------
    default_repo : str
        default github repository repo name

    """
    return 'MODFLOW-USGS/executables'


def get_default_json(tag_name=None):
    """
    Return a default github api json for the provided release tag_name in a
    github repository.

    Parameters
    ----------
    tag_name : str
        github repository release tag

    Returns
    -------
    json_obj : dict
        json object (dictionary) with a tag_name and assets including
        file names and download links

    """
    if tag_name is None:
        tag_name = '3.0'
    url = ('https://github.com/{}/'.format(get_default_repo()) +
           'releases/download/{}/'.format(tag_name))
    json_obj = {'tag_name': tag_name}

    # define asset names and paths for assets
    names = ['mac.zip', 'linux.zip', 'win32.zip', 'win64.zip']
    paths = [url + p for p in names]

    assets_list = []
    for name, path in zip(names, paths):
        assets_list.append({'name': name, 'browser_download_url': path})
    json_obj['assets'] = assets_list

    return json_obj


def get_request_json(request_url):
    """
    Process a url request and return a json if successful.

    Parameters
    ----------
    request_url : str
        url for request

    Returns
    -------
    success : bool
        boolean indicating if the requat failed

    status_code: integer
        request status code

    json_obj : dict
        json object

    """
    import requests
    import json

    json_obj = None
    success = True

    # open request
    r = requests.get(request_url)

    # connection established - retrieve the json
    if r.ok:
        json_obj = json.loads(r.text or r.content)
    else:
        success = r.status_code == requests.codes.ok

    return success, r, json_obj


def repo_json(github_repo, tag_name=None):
    """
    Return the github api json for the latest github release in a
    github repository.

    Parameters
    ----------
    github_repo : str
        Repository name, such as MODFLOW-USGS/modflow6

    tag_name : str
        github repository release tag

    Returns
    -------
    json_obj : dict
        json object (dictionary) with a tag_name and assets including
        file names and download links

    """
    import requests
    repo_url = 'https://api.github.com/repos/{}'.format(github_repo)

    if tag_name is None:
        request_url = '{}/releases/latest'.format(repo_url)
    else:
        request_url = '{}/releases'.format(repo_url)
        success, r, json_cat = get_request_json(request_url)
        if success:
            request_url = None
            for release in json_cat:
                if release['tag_name'] == tag_name:
                    request_url = release['url']
                    break
            if request_url is None:
                msg = "Could not find tag_name ('{}') ".format(tag_name) + \
                      "in release catalog"
                raise Exception(msg)
        else:
            msg = 'Could not get release catalog from ' + request_url
            raise Exception(msg)

    msg = "Requesting asset data for tag_name '{}' ".format(tag_name) + \
          "from: {}".format(request_url)
    print(msg)

    # process the request
    success, r, json_obj = get_request_json(request_url)

    # connection established - get the requested data
    if not success:
        if r.status_code != requests.codes.ok:
            msg = r.text['message']
            if 'API rate limit exceeded' in msg:
                print(msg + '\n will use default values.')
                if github_repo == get_default_repo():
                    json_obj = get_default_json(tag_name)
            else:
                msg = 'Could not find latest executables from ' + request_url
                print(msg)
                r.raise_for_status()

    # return json object
    return json_obj


def get_repo_assets(github_repo=None, version=None):
    """
    Return a dictionary containing the file name and the link to the asset
    contained in a github repository.

    Parameters
    ----------
    github_repo : str
        Repository name, such as MODFLOW-USGS/modflow6. If github_repo is
        None set to 'MODFLOW-USGS/executables'

    version : str
        github repository release tag


    Returns
    -------
    result_dict : dict
        dictionary of file names and links

    """
    if github_repo is None:
        github_repo = get_default_repo()

    # get json and extract assets
    json_obj = repo_json(github_repo, tag_name=version)
    assets = json_obj['assets']

    # build simple assets dictionary
    result_dict = {}
    for asset in assets:
        k = asset['name']
        v = asset['browser_download_url']
        result_dict[k] = v

    return result_dict


def repo_latest_version(github_repo=None):
    """
    Return a string of the latest version number (tag) contained in a
    github repository release.

    Parameters
    ----------
    github_repo : str
        Repository name, such as MODFLOW-USGS/modflow6. If github_repo is
        None set to 'MODFLOW-USGS/executables'

    Returns
    -------
    version : str
        string with the latest version/tag number

    """
    if github_repo is None:
        github_repo = get_default_repo()

    # get json
    json_obj = repo_json(github_repo)

    return json_obj['tag_name']


def getmfexes(pth='.', version=None, platform=None, exes=None):
    """
    Get the latest MODFLOW binary executables from a github site
    (https://github.com/MODFLOW-USGS/executables) for the specified
    operating system and put them in the specified path.

    Parameters
    ----------
    pth : str
        Location to put the executables (default is current working directory)

    version : str
        Version of the MODFLOW-USGS/executables release to use. If version is
        None the github repo will be queried for the version number.

    platform : str
        Platform that will run the executables.  Valid values include mac,
        linux, win32 and win64.  If platform is None, then routine will
        download the latest asset from the github repository.

    exes : str or list of strings
        executable or list of executables to retain

    """
    # set download directory to path in case a selection of files
    download_dir = pth

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
        msg = 'unknown platform detected ({})'.format(platform)
        success = platform in ['mac', 'linux', 'win32', 'win64']
        if not success:
            raise ValueError(msg)
    zipname = '{}.zip'.format(platform)

    # Evaluate exes keyword
    if exes is not None:
        download_dir = os.path.join('.', 'download_dir')
        if isinstance(exes, str):
            exes = tuple(exes)
        elif isinstance(exes, (int, float)):
            msg = 'exes keyword must be a string or a list/tuple of strings'
            raise TypeError(msg)

    # Determine path for file download and then download and unzip
    assets = get_repo_assets(github_repo=get_default_repo(),
                             version=version)
    download_url = assets[zipname]
    download_and_unzip(download_url, download_dir)

    if exes is not None:
        # make sure pth exists
        if not os.path.exists(pth):
            print('Creating the directory:\n    {}'.format(pth))
            os.makedirs(pth)

        # move select files to pth
        for f in os.listdir(download_dir):
            src = os.path.join(download_dir, f)
            dst = os.path.join(pth, f)
            for exe in exes:
                if exe in f:
                    shutil.move(src, dst)
                    break

        # remove the download directory
        if os.path.isdir(download_dir):
            print('Removing folder ' + download_dir)
            shutil.rmtree(download_dir)

    return
