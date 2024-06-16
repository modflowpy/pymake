import contextlib
import os
import re
from importlib import metadata
from pathlib import Path

import pytest

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
