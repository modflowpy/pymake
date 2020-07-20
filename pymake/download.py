import os
import sys
import shutil
import time
import timeit
import requests
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import tarfile


class pymakeZipFile(ZipFile):
    """ZipFile file attributes are not being preserved.

    This class preserves file attributes as described on StackOverflow at
    https://stackoverflow.com/questions/39296101/python-zipfile-removes-execute-permissions-from-binaries

    """

    def extract(self, member, path=None, pwd=None):
        """

        Parameters
        ----------
        member : str
            individual file to extract. If member does not exist, all files
            are extracted.
        path : str
            directory path to extract file in a zip file (default is None,
            which results in files being extracted in the current directory)
        pwd : str
            zip file password (default is None)

        Returns
        -------
        ret_val : int
            return value indicating status of file extraction

        """
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
        """Extract all files in the zipfile.

        Parameters
        ----------
        path : str
            directory path to extract files in a zip file (default is None,
            which results in files being extracted in the current directory)
        members : str
            individual files to extract (default is None, which extracts
            all members)
        pwd : str
            zip file password (default is None)

        Returns
        -------

        """
        if members is None:
            members = self.namelist()

        if path is None:
            path = os.getcwd()
        else:
            if hasattr(os, "fspath"):
                # introduced in python 3.6 and above
                path = os.fspath(path)

        for zipinfo in members:
            self.extract(zipinfo, path, pwd)

    @staticmethod
    def compressall(path, file_pths=None, dir_pths=None, patterns=None):
        """Compress selected files or files in selected directories.

        Parameters
        ----------
        path : str
            output zip file path
        file_pths : str or list of str
            file paths to include in the output zip file (default is None)
        dir_pths : str or list of str
            directory paths to include in the output zip file (default is None)
        patterns : str or list of str
            file patterns to include in the output zip file (default is None)

        Returns
        -------
        success : bool
            boolean indicating if the output zip file was created

        """

        # create an empty list
        if file_pths is None:
            file_pths = []
        # convert files to a list
        else:
            if isinstance(file_pths, str):
                file_pths = [file_pths]
            elif isinstance(file_pths, tuple):
                file_pths = list(file_pths)

        # remove directories from the file list
        if len(file_pths) > 0:
            file_pths = [e for e in file_pths if os.path.isfile(e)]

        # convert dirs to a list if a str (a tuple is allowed)
        if dir_pths is None:
            dir_pths = []
        else:
            if isinstance(dir_pths, str):
                dir_pths = [dir_pths]

        # convert find to a list if a str (a tuple is allowed)
        if patterns is not None:
            if isinstance(patterns, str):
                patterns = [patterns]

        # walk through dirs and add files to the list
        for dir_pth in dir_pths:
            for dirname, subdirs, files in os.walk(dir_pth):
                for filename in files:
                    fpth = os.path.join(dirname, filename)
                    # add the file if it does not exist in file_pths
                    if fpth not in file_pths:
                        file_pths.append(fpth)

        # remove file_paths that do not match the patterns
        if patterns is not None:
            tlist = []
            for file_pth in file_pths:
                if any(p in os.path.basename(file_pth) for p in patterns):
                    tlist.append(file_pth)
            file_pths = tlist

        # write the zipfile
        success = True
        if len(file_pths) > 0:
            zf = ZipFile(path, "w", ZIP_DEFLATED)

            # write files to zip file
            for file_pth in file_pths:
                arcname = os.path.basename(file_pth)
                zf.write(file_pth, arcname=arcname)

            # close the zip file
            zf.close()
        else:
            msg = "No files to add to the zip file"
            print(msg)
            success = False

        return success


def request_get(url, verify, timeout, max_requests, verbose):
    """Make a url request

    Parameters
    ----------
    url : str
        url address for the zip file
    verify : bool
        boolean indicating if the url request should be verified
    timeout : int
        url request time out length (default is 30 seconds)
    max_requests : int
        number of url download request attempts (default is 10)
    verbose : bool
        boolean indicating if output will be printed to the terminal

    Returns
    -------
    req : request object
        request object for url

    """
    for idx in range(max_requests):
        if verbose:
            msg = "open request attempt {} of {}".format(idx + 1, max_requests)
            print(msg)
        try:
            req = requests.get(
                url, stream=True, verify=verify, timeout=timeout
            )
        except:
            if idx < max_requests - 1:
                time.sleep(13)
                continue
            else:
                msg = "Cannot open request from:\n" + "    {}\n\n".format(url)
                print(msg)
                req.raise_for_status()

        # successful request
        break

    return req


def download_and_unzip(
    url,
    pth="./",
    delete_zip=True,
    verify=True,
    timeout=30,
    max_requests=10,
    chunk_size=2048000,
    verbose=False,
):
    """Download and unzip a zip file from a url.

    Parameters
    ----------
    url : str
        url address for the zip file
    pth : str
        path where the zip file will be saved (default is the current path)
    delete_zip : bool
        boolean indicating if the zip file should be deleted after it is
        unzipped (default is True)
    verify : bool
        boolean indicating if the url request should be verified
    timeout : int
        url request time out length (default is 30 seconds)
    max_requests : int
        number of url download request attempts (default is 10)
    chunk_size : int
        maximum url download request chunk size (default is 2048000 bytes)
    verbose : bool
        boolean indicating if output will be printed to the terminal

    Returns
    -------

    """
    # create download directory
    if not os.path.exists(pth):
        if verbose:
            print("Creating the directory:\n    {}".format(pth))
        os.makedirs(pth)

    if verbose:
        print("Attempting to download the file:\n    {}".format(url))

    # define the filename
    file_name = os.path.join(pth, url.split("/")[-1])

    # download the file
    success = False
    tic = timeit.default_timer()

    # open request
    req = request_get(url, verify, timeout, max_requests, verbose)

    # get content length
    tag = "Content-length"
    if tag in req.headers:
        fs = req.headers[tag]
        lenfs = len(fs)
        fs = int(fs)

        bfmt = "{:" + "{}".format(lenfs) + ",d}"
        sbfmt = "{:>" + "{}".format(len(bfmt.format(int(fs)))) + "s} bytes"
        msg = "   file size: {}".format(sbfmt.format(bfmt.format(int(fs))))
        if verbose:
            print(msg)
    else:
        msg = "'{}' header not available from '{}'".format(tag, url)
        raise Exception(msg)

    if fs <= 0:
        msg = "invalid request file size ({}) from '{}'".format(fs, url)
        raise Exception(msg)

    # download data from url
    for idx in range(max_requests):
        # print download attempt message
        if verbose:
            print(" download attempt: {}".format(idx + 1))

        # connection established - download the file
        ds = 0
        try:
            with open(file_name, "wb") as f:
                for chunk in req.iter_content(chunk_size=chunk_size):
                    if chunk:
                        ds += len(chunk)
                        if fs > 0:
                            msg = (
                                "     downloaded "
                                + sbfmt.format(bfmt.format(ds))
                                + " of "
                                + bfmt.format(int(fs))
                                + " bytes"
                                + " ({:10.4%})".format(float(ds) / float(fs))
                            )
                            if verbose:
                                print(msg)
                            else:
                                sys.stdout.write(".")
                                sys.stdout.flush()
                        f.write(chunk)

                # check that the entire file has been downloaded
                if ds == fs:
                    success = True
                else:
                    continue
        except:
            # reestablish request
            req = request_get(url, verify, timeout, max_requests, verbose)

            # try to download the data again
            continue

        # terminate the download attempt loop
        if success:
            break

    # write the total download time
    toc = timeit.default_timer()
    tsec = toc - tic
    if verbose:
        print("\ntotal download time: {} seconds".format(tsec))

    if success:
        if fs > 0:
            if verbose:
                print("download speed:      {} MB/s".format(fs / (1e6 * tsec)))
    else:
        msg = "could not download...{}".format(url)
        raise ConnectionError(msg)

    # Unzip the file, and delete zip file if successful.
    if "zip" in os.path.basename(file_name) or "exe" in os.path.basename(
        file_name
    ):
        z = pymakeZipFile(file_name)
        try:
            # write a message
            if not verbose:
                sys.stdout.write("\n")
            print("uncompressing...'{}'".format(file_name))

            # extract the files
            z.extractall(pth)
        except:
            p = "Could not unzip the file.  Stopping."
            raise Exception(p)
        z.close()
    elif "tar" in os.path.basename(file_name):
        ar = tarfile.open(file_name)
        ar.extractall(path=pth)
        ar.close()

    # delete the zipfile
    if delete_zip:
        if verbose:
            print("Deleting the zipfile...")
        os.remove(file_name)

    if verbose:
        print("Done downloading and extracting...\n")

    return success


def zip_all(path, file_pths=None, dir_pths=None, patterns=None):
    """Compress all files in the user-provided list of file paths and directory
    paths that match the provided file patterns.

    Parameters
    ----------
    path : str
        path of the zip file that will be created

    file_pths : str or list
        file path or list of file paths to be compressed

    dir_pths : str or list
        directory path or list of directory paths to search for files that
        will be compressed

    patterns : str or list
        file pattern or list of file patterns s to match to when creating a
        list of files that will be compressed

    Returns
    -------

    """
    return pymakeZipFile.compressall(
        path, file_pths=file_pths, dir_pths=dir_pths, patterns=patterns
    )


def get_default_repo():
    """Return the default repo name.

    Returns
    -------
    default_repo : str
        default github repository repo name

    """
    return "MODFLOW-USGS/executables"


def get_default_json(tag_name=None):
    """Return a default github api json for the provided release tag_name in a
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
        tag_name = "4.0"
    url = "https://github.com/{}/".format(
        get_default_repo()
    ) + "releases/download/{}/".format(tag_name)
    json_obj = {"tag_name": tag_name}

    # define asset names and paths for assets
    names = ["mac.zip", "linux.zip", "win32.zip", "win64.zip"]
    paths = [url + p for p in names]

    assets_list = []
    for name, path in zip(names, paths):
        assets_list.append({"name": name, "browser_download_url": path})
    json_obj["assets"] = assets_list

    return json_obj


def get_request_json(request_url):
    """Process a url request and return a json if successful.

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
    import json

    nattempts = 10
    json_obj = None
    success = True

    # open request
    for idx in range(nattempts):
        req = requests.get(request_url)
        if req.status_code != 200:
            if idx < nattempts - 1:
                time.sleep(13)
                continue
            else:
                msg = "Cannot open request from:\n    {}\n\n".format(
                    request_url
                )
                print(msg)
                req.raise_for_status()

    # connection established - retrieve the json
    if req.ok:
        json_obj = json.loads(req.text or req.content)
    else:
        success = req.status_code == requests.codes.ok

    return success, req, json_obj


def repo_json(github_repo, tag_name=None, error_return=False, verbose=False):
    """Return the github api json for the latest github release in a github
    repository.

    Parameters
    ----------
    github_repo : str
        Repository name, such as MODFLOW-USGS/modflow6
    tag_name : str
        github repository release tag
    error_return : bool
        boolean indicating if None will be returned if there are GitHub API
        issues
    verbose : bool
        boolean indicating if output will be printed to the terminal

    Returns
    -------
    json_obj : dict
        json object (dictionary) with a tag_name and assets including
        file names and download links

    """
    repo_url = "https://api.github.com/repos/{}".format(github_repo)

    if tag_name is None:
        request_url = "{}/releases/latest".format(repo_url)
    else:
        request_url = "{}/releases".format(repo_url)
        success, r, json_cat = get_request_json(request_url)
        if success:
            request_url = None
            for release in json_cat:
                if release["tag_name"] == tag_name:
                    request_url = release["url"]
                    break
            if request_url is None:
                msg = (
                    "Could not find tag_name ('{}') ".format(tag_name)
                    + "in release catalog"
                )
                if error_return:
                    print(msg)
                    return None
                else:
                    raise Exception(msg)
        else:
            msg = "Could not get release catalog from " + request_url
            if error_return:
                if verbose:
                    print(msg)
                return None
            else:
                raise Exception(msg)

    msg = "Requesting asset data "
    if tag_name is not None:
        msg += "for tag_name '{}' ".format(tag_name)
    msg += "from: {}".format(request_url)
    if verbose:
        print(msg)

    # process the request
    success, req, json_obj = get_request_json(request_url)

    # evaluate request errors
    if not success:
        if github_repo == get_default_repo():
            msg = "will use default values for {}".format(github_repo)
            if verbose:
                print(msg)
            json_obj = get_default_json(tag_name)
        else:
            msg = "Could not find json from " + request_url
            if verbose:
                print(msg)
            if error_return:
                json_obj = None
            else:
                req.raise_for_status()

    # return json object
    return json_obj


def get_repo_assets(github_repo=None, version=None, error_return=False):
    """Return a dictionary containing the file name and the link to the asset
    contained in a github repository.

    Parameters
    ----------
    github_repo : str
        Repository name, such as MODFLOW-USGS/modflow6. If github_repo is
        None set to 'MODFLOW-USGS/executables'
    version : str
        github repository release tag
    error_return : bool
        boolean indicating if None will be returned if there are GitHub API
        issues

    Returns
    -------
    result_dict : dict
        dictionary of file names and links

    """
    if github_repo is None:
        github_repo = get_default_repo()

    # get json and extract assets
    json_obj = repo_json(
        github_repo, tag_name=version, error_return=error_return
    )
    if json_obj is None:
        result_dict = None
    else:
        assets = json_obj["assets"]

        # build simple assets dictionary
        result_dict = {}
        for asset in assets:
            k = asset["name"]
            v = asset["browser_download_url"]
            result_dict[k] = v

    return result_dict


def repo_latest_version(github_repo=None):
    """Return a string of the latest version number (tag) contained in a github
    repository release.

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

    return json_obj["tag_name"]


def getmfexes(pth=".", version=None, platform=None, exes=None, verbose=False):
    """Get the latest MODFLOW binary executables from a github site
    (https://github.com/MODFLOW-USGS/executables) for the specified operating
    system and put them in the specified path.

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
    verbose : bool
        boolean indicating if output will be printed to the terminal

    """
    # set download directory to path in case a selection of files
    download_dir = pth

    # Determine the platform in order to construct the zip file name
    if platform is None:
        if sys.platform.lower() == "darwin":
            platform = "mac"
        elif sys.platform.lower().startswith("linux"):
            platform = "linux"
        elif "win" in sys.platform.lower():
            is_64bits = sys.maxsize > 2 ** 32
            if is_64bits:
                platform = "win64"
            else:
                platform = "win32"
        else:
            errmsg = (
                "Could not determine platform"
                ".  sys.platform is {}".format(sys.platform)
            )
            raise Exception(errmsg)
    else:
        msg = "unknown platform detected ({})".format(platform)
        success = platform in ["mac", "linux", "win32", "win64"]
        if not success:
            raise ValueError(msg)
    zipname = "{}.zip".format(platform)

    # Evaluate exes keyword
    if exes is not None:
        download_dir = os.path.join(".", "download_dir")
        if isinstance(exes, str):
            exes = tuple(exes)
        elif isinstance(exes, (int, float)):
            msg = "exes keyword must be a string or a list/tuple of strings"
            raise TypeError(msg)

    # Determine path for file download and then download and unzip
    assets = get_repo_assets(github_repo=get_default_repo(), version=version)
    download_url = assets[zipname]
    download_and_unzip(download_url, download_dir, verbose=verbose)

    if exes is not None:
        # make sure pth exists
        if not os.path.exists(pth):
            if verbose:
                print("Creating the directory:\n    {}".format(pth))
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
            if verbose:
                print("Removing folder " + download_dir)
            shutil.rmtree(download_dir)

    return
