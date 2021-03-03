import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--runall",
        action="store_true",
        default=False,
        help="run complete suite of tests",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "all: mark all tests to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runall"):
        # --runall given in cli: do not skip any tests
        return
    skip_test = pytest.mark.skip(reason="need --runall option to run")
    for item in items:
        if "all" in item.keywords:
            item.add_marker(skip_test)
