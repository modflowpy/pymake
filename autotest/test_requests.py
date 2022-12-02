# Test the download_and_unzip functionality of pymake
import os
import shutil
import sys

import pytest

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


@pytest.mark.requests
def test_latest_version():
    version = pymake.repo_latest_version()
    test_version = "5.0"
    msg = (
        f"returned version ({version}) "
        + "is not greater than or equal to "
        + f"defined version ({test_version})"
    )
    if version is not None:
        assert float(version) >= float(test_version), msg
        print(f"returned version...{version}")
    return


@pytest.mark.requests
def test_latest_assets():
    mfexes_repo_name = "MODFLOW-USGS/executables"
    assets = pymake.get_repo_assets(mfexes_repo_name)
    keys = assets.keys()
    test_keys = [
        "code.json",
        "mac.zip",
        "linux.zip",
        "win32.zip",
        "win64.zip",
    ]
    for key in keys:
        print(f"evaluating the availability of...{key}")
        msg = f"unknown key ({key}) found in github repo assets"
        assert key in test_keys, msg
    return


@pytest.mark.requests
def test_previous_assets():
    # hack for failure of OSX on github actions
    env = "GITHUB_ACTIONS"
    # os.environ[env] = "true"
    allow_failure = False
    if env in os.environ:
        if sys.platform.lower() == "darwin":
            if os.environ.get(env) == "true":
                allow_failure = True

    mfexes_repo_name = "MODFLOW-USGS/modflow6"
    version = "6.1.0"
    assets = pymake.get_repo_assets(
        mfexes_repo_name, version=version, error_return=True
    )
    msg = (
        "failed to get release {} ".format(version)
        + f"from the '{mfexes_repo_name}' repo"
    )
    if allow_failure:
        if not isinstance(assets, dict):
            print(msg)
        else:
            print(f"available assets: {', '.join(assets.keys())}")
    else:
        assert isinstance(assets, dict), msg
        print(f"available assets: {', '.join(assets.keys())}")


@pytest.mark.requests
def test_mfexes_download_and_unzip_and_zip():
    exclude_files = [
        "code.json",
        "prms_constants.f90",
        "prms_summary.f90",
        "prms_time.f90",
        "utils_prms.f90",
    ]
    pth = os.path.join(
        f"temp_mfexes_{os.path.basename(__file__).replace('.py', '')}"
    )
    pymake.getmfexes(pth, verbose=True)
    for f in os.listdir(pth):
        fpth = os.path.join(pth, f)
        if not os.path.isdir(fpth) and f not in exclude_files:
            errmsg = f"{fpth} not executable"
            assert which(fpth) is not None, errmsg

    # zip up exe's using files
    zip_pth = os.path.join(
        f"temp_mfexes_{os.path.basename(__file__).replace('.py', '')}",
        "ziptest01.zip",
    )
    print(f"creating '{zip_pth}'")
    success = pymake.zip_all(
        zip_pth, file_pths=[os.path.join(pth, e) for e in os.listdir(pth)]
    )
    assert success, "could not create zipfile using file names"
    os.remove(zip_pth)

    # zip up exe's using directories
    zip_pth = os.path.join(
        f"temp_mfexes_{os.path.basename(__file__).replace('.py', '')}",
        "ziptest02.zip",
    )
    print(f"creating '{zip_pth}'")
    success = pymake.zip_all(zip_pth, dir_pths=pth)
    assert success, "could not create zipfile using directories"
    os.remove(zip_pth)

    # zip up exe's using directories and a pattern
    zip_pth = os.path.join(
        f"temp_mfexes_{os.path.basename(__file__).replace('.py', '')}",
        "ziptest03.zip",
    )
    print(f"creating '{zip_pth}'")
    success = pymake.zip_all(zip_pth, dir_pths=pth, patterns="mf")
    assert success, "could not create zipfile using directories and a pattern"
    os.remove(zip_pth)

    # zip up exe's using files and directories
    zip_pth = os.path.join(
        f"temp_mfexes_{os.path.basename(__file__).replace('.py', '')}",
        "ziptest04.zip",
    )
    print(f"creating '{zip_pth}'")
    success = pymake.zip_all(
        zip_pth,
        file_pths=[os.path.join(pth, e) for e in os.listdir(pth)],
        dir_pths=pth,
    )
    assert success, "could not create zipfile using files and directories"
    os.remove(zip_pth)

    # clean up exe's
    for f in os.listdir(pth):
        fpth = os.path.join(pth, f)
        if not os.path.isdir(fpth):
            print("Removing " + f)
            os.remove(fpth)

    # clean up directory
    if os.path.isdir(pth):
        print("Removing folder " + pth)
        shutil.rmtree(pth)

    return


@pytest.mark.requests
def test_nightly_download_and_unzip():
    exclude_files = ["code.json"]
    pth = os.path.join(
        f"temp_nightly_{os.path.basename(__file__).replace('.py', '')}"
    )
    pymake.getmfnightly(pth, verbose=True)
    for f in os.listdir(pth):
        fpth = os.path.join(pth, f)
        print(f"downloaded: {fpth}")
        if not os.path.isdir(fpth) and f not in exclude_files:
            errmsg = f"{fpth} not executable"
            assert which(fpth) is not None, errmsg

    # clean up directory
    if os.path.isdir(pth):
        print("\nRemoving folder " + pth)
        shutil.rmtree(pth)


if __name__ == "__main__":
    # test_previous_assets()
    test_latest_version()
    # test_latest_assets()
    # test_nightly_download_and_unzip()
    # test_download_and_unzip_and_zip()
