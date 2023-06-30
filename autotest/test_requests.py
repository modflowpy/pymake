# Test the download_and_unzip functionality of pymake
import json
import os
import shutil
import subprocess
import sys

import pytest
from flaky import flaky

import pymake

RERUNS = 3


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


def export_code_json(function_tmpdir, file_name="code.json"):
    # make the json file
    fpth = function_tmpdir / file_name
    pymake.usgs_program_data.export_json(
        fpth=fpth,
        current=True,
        write_markdown=True,
        verbose=True,
    )

    # check that the json file was made
    msg = f"did not make...{fpth}"
    assert os.path.isfile(fpth), msg

    return fpth


def run_cli_cmd(cmd: list) -> None:
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

    assert (
        process.returncode == 0
    ), f"'{' '.join(cmd)}' failed\n\tstatus code {process.returncode}\n"
    return


@pytest.mark.dependency("latest_version")
@flaky(max_runs=RERUNS)
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


@pytest.mark.dependency("latest_assets")
@flaky(max_runs=RERUNS)
@pytest.mark.requests
def test_latest_assets():
    mfexes_repo_name = "MODFLOW-USGS/executables"
    assets = pymake.get_repo_assets(mfexes_repo_name)
    keys = assets.keys()
    test_keys = [
        "code.json",
        "code.md",
        "mac.zip",
        "linux.zip",
        "win64.zip",
    ]
    for key in keys:
        print(f"evaluating the availability of...{key}")
        msg = f"unknown key ({key}) found in github repo assets"
        assert key in test_keys, msg
    return


@pytest.mark.dependency("previous_assets")
@flaky(max_runs=RERUNS)
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


@pytest.mark.dependency("mfexes")
@flaky(max_runs=RERUNS)
@pytest.mark.requests
def test_mfexes_download_and_unzip_and_zip(function_tmpdir):
    exclude_files = [
        "code.json",
        "prms_constants.f90",
        "prms_summary.f90",
        "prms_time.f90",
        "utils_prms.f90",
    ]
    pth = str(function_tmpdir)
    pymake.getmfexes(pth, verbose=True)
    for f in os.listdir(pth):
        fpth = os.path.join(pth, f)
        if not os.path.isdir(fpth) and f not in exclude_files:
            errmsg = f"{fpth} not executable"
            assert which(fpth) is not None, errmsg

    # zip up exe's using files
    zip_pth = function_tmpdir / "ziptest01.zip"
    print(f"creating '{zip_pth}'")
    success = pymake.zip_all(
        zip_pth, file_pths=[os.path.join(pth, e) for e in os.listdir(pth)]
    )
    assert success, "could not create zipfile using file names"
    os.remove(zip_pth)

    # zip up exe's using directories
    zip_pth = function_tmpdir / "ziptest02.zip"
    print(f"creating '{zip_pth}'")
    success = pymake.zip_all(zip_pth, dir_pths=pth)
    assert success, "could not create zipfile using directories"
    os.remove(zip_pth)

    # zip up exe's using directories and a pattern
    zip_pth = function_tmpdir / "ziptest03.zip"
    print(f"creating '{zip_pth}'")
    success = pymake.zip_all(zip_pth, dir_pths=pth, patterns="mf")
    assert success, "could not create zipfile using directories and a pattern"
    os.remove(zip_pth)

    # zip up exe's using files and directories
    zip_pth = function_tmpdir / "ziptest04.zip"
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


@pytest.mark.dependency("nightly_download")
@flaky(max_runs=RERUNS)
@pytest.mark.requests
def test_nightly_download_and_unzip(function_tmpdir):
    exclude_files = ["code.json"]
    pth = str(function_tmpdir)
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


@pytest.mark.dependency("usgsprograms")
@flaky(max_runs=RERUNS)
@pytest.mark.requests
def test_usgsprograms():
    print("test_usgsprograms()")
    upd = pymake.usgs_program_data().get_program_dict()

    all_keys = list(upd.keys())

    get_keys = pymake.usgs_program_data.get_keys()

    msg = "the keys from program_dict are not equal to .get_keys()"
    assert all_keys == get_keys, msg


@pytest.mark.dependency("target_key_error")
@flaky(max_runs=RERUNS)
@pytest.mark.requests
def test_target_key_error():
    print("test_target_key_error()")
    with pytest.raises(KeyError):
        pymake.usgs_program_data.get_target("error")


@pytest.mark.dependency("target_keys")
@flaky(max_runs=RERUNS)
@pytest.mark.requests
def test_target_keys():
    print("test_target_keys()")
    prog_dict = pymake.usgs_program_data().get_program_dict()
    targets = pymake.usgs_program_data.get_keys()
    for target in targets:
        target_dict = pymake.usgs_program_data.get_target(target)
        test_dict = prog_dict[target]

        msg = (
            f"dictionary from {target} "
            + "does not match dictionary from .get_target()"
        )
        assert target_dict == test_dict, msg


@pytest.mark.dependency("export_json")
@flaky(max_runs=RERUNS)
@pytest.mark.requests
def test_usgsprograms_export_json(function_tmpdir):
    os.chdir(function_tmpdir)

    # export code.json and return json file path
    fpth = export_code_json(function_tmpdir, file_name="code.export.json")

    # test the json export
    with open(fpth, "r") as f:
        json_dict = json.load(f)
    json_keys = list(json_dict.keys())

    current_keys = pymake.usgs_program_data.get_keys(current=True)

    msg = "the number of current keys is not equal to json keys"
    assert len(json_keys) == len(current_keys), msg

    prog_dict = pymake.usgs_program_data().get_program_dict()
    for key, value in json_dict.items():
        temp_dict = prog_dict[key]
        # fill keys that are programmatically filled
        fill_keys = ("url_download_asset_date",)
        for fill_key in fill_keys:
            temp_dict[fill_key] = value[fill_key]
        msg = (
            f"json dictionary for {key} key "
            + "is not equal to the .usgs_prog_data dictionary"
        )
        assert value == temp_dict, msg


@pytest.mark.dependency("load_json_error")
@flaky(max_runs=RERUNS)
@pytest.mark.requests
def test_usgsprograms_load_json_error(function_tmpdir):
    fpth = function_tmpdir / "code.test.error.json"
    my_dict = {"mf2005": {"bad": 12, "key": True}}
    pymake.usgs_program_data.export_json(
        fpth=fpth, prog_data=my_dict, update=False
    )

    with pytest.raises(KeyError):
        pymake.usgs_program_data.load_json(fpth=fpth)


@pytest.mark.dependency("load_json")
@flaky(max_runs=RERUNS)
@pytest.mark.requests
def test_usgsprograms_load_json(function_tmpdir):
    os.chdir(function_tmpdir)

    # export code.json and return json file path
    fpth = export_code_json(function_tmpdir, file_name="code.load.json")

    json_dict = pymake.usgs_program_data.load_json(fpth)

    # check that the json file was loaded
    msg = f"could not load {fpth}"
    assert json_dict is not None, msg


@pytest.mark.dependency("list_json_error")
@flaky(max_runs=RERUNS)
@pytest.mark.requests
def test_usgsprograms_list_json_error(function_tmpdir):
    os.chdir(function_tmpdir)

    fpth = function_tmpdir / "does.not.exist.json"
    with pytest.raises(IOError):
        pymake.usgs_program_data.list_json(fpth=fpth)


@pytest.mark.dependency("list_json")
@flaky(max_runs=RERUNS)
@pytest.mark.requests
def test_usgsprograms_list_json(function_tmpdir):
    os.chdir(function_tmpdir)

    # export code.json and return json file path
    fpth = export_code_json(function_tmpdir, file_name="code.list.json")

    # list the contents of the json file
    pymake.usgs_program_data.list_json(fpth=fpth)


@pytest.mark.dependency("shared")
@flaky(max_runs=RERUNS)
@pytest.mark.requests
def test_shared():
    print("test_shared()")
    target_dict = pymake.usgs_program_data.get_target("libmf6")
    assert target_dict.shared_object, "libmf6 is a shared object"


@pytest.mark.dependency("not_shared")
@flaky(max_runs=RERUNS)
@pytest.mark.requests
def test_not_shared():
    print("test_not_shared()")
    target_dict = pymake.usgs_program_data.get_target("mf6")
    assert not target_dict.shared_object, "mf6 is not a shared object"


@pytest.mark.dependency(name="code_json")
@flaky(max_runs=RERUNS)
@pytest.mark.requests
def test_code_json(function_tmpdir) -> None:
    os.chdir(function_tmpdir)

    cmd = ["make-code-json", "-f", f"{function_tmpdir / 'code.json'}"]
    run_cli_cmd(cmd)
