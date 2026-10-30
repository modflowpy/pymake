import re
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path

import pytest

from pymake.utils._compiler_switches import _get_base_compiler_name

# import modflow-devtools fixtures

pytest_plugins = ["modflow_devtools.fixtures"]


# constants


# misc utilities
def get_pymake_appdir():
    appdir = Path.home() / ".pymake"
    appdir.mkdir(parents=True, exist_ok=True)
    return appdir


def get_project_root_path() -> Path:
    return Path(__file__).parent.parent


# path fixtures


# build check fixtures


@pytest.fixture
def check_static_intel():
    """Return a function asserting an executable built with an intel
    compiler on linux doesn't need the intel runtime shared libraries.

    The intel runtime is installed wherever the tests run, so a
    dynamically linked executable still runs fine there; only its
    dynamic section shows the problem.

    """

    def check(exe, fc):
        if sys.platform != "linux":
            pytest.skip("only checked on linux")
        if _get_base_compiler_name(fc) not in ("ifort", "mpiifort", "ifx", "mpiifx"):
            pytest.skip("only checked for intel compilers")
        if shutil.which("readelf") is None:
            pytest.skip("readelf not available")
        out = subprocess.run(
            ["readelf", "-d", str(exe)], capture_output=True, text=True, check=True
        ).stdout
        needed = re.findall(r"\(NEEDED\)\s+Shared library: \[(.+?)\]", out)
        intel = [lib for lib in needed if re.match(r"lib(ifcore|ifport|imf)", lib)]
        assert not intel, f"{exe} links the intel runtime dynamically: {intel}"

    return check


# pytest configuration hooks


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    # this is necessary so temp dir fixtures can
    # inspect test results and check for failure
    # (see https://doc.pytest.org/en/latest/example/simple.html#making-test-result-information-available-in-fixtures)

    outcome = yield
    rep = outcome.get_result()

    # report attribute for each phase (setup, call, teardown)
    # we're only interested in result of the function call
    setattr(item, "rep_" + rep.when, rep)


def pytest_report_header(config):
    """Header for pytest to show versions of packages."""
    required = []
    extra = {}
    for item in metadata.requires("flopy"):
        pkg_name = re.findall(r"[a-z0-9_\-]+", item, re.IGNORECASE)[0]
        if res := re.findall("extra == ['\"](.+)['\"]", item):
            assert len(res) == 1, item
            pkg_extra = res[0]
            if pkg_extra not in extra:
                extra[pkg_extra] = []
            extra[pkg_extra].append(pkg_name)
        else:
            required.append(pkg_name)

    processed = set()
    lines = []
    items = []
    for name in required:
        processed.add(name)
        try:
            version = metadata.version(name)
            items.append(f"{name}-{version}")
        except metadata.PackageNotFoundError:
            items.append(f"{name} (not found)")
    lines.append("required packages: " + ", ".join(items))
    installed = []
    not_found = []
    for name in extra["optional"]:
        if name in processed:
            continue
        processed.add(name)
        try:
            version = metadata.version(name)
            installed.append(f"{name}-{version}")
        except metadata.PackageNotFoundError:
            not_found.append(name)
    if installed:
        lines.append("optional packages: " + ", ".join(installed))
    if not_found:
        lines.append("optional packages not found: " + ", ".join(not_found))
    return "\n".join(lines)


def pytest_addoption(parser):
    parser.addoption(
        "--exclude",
        action="store",
        default="",
        help="forwarded to --exclude when testing 'make-program :'",
    )
