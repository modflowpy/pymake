import argparse
import re
import textwrap
from datetime import datetime
from pathlib import Path

from filelock import FileLock
from packaging.version import Version

_epilog = """\
Update version information stored in version.txt in the project root
and other files in the repository. If --version is not provided, the
version number will not be changed. The version tag must comply with
'<major>.<minor>.<patch>' format convention for semantic versioning.
To show the version without changing anything, use --get (short -g).
"""
_project_name = "mfpymake"
_project_root_path = Path(__file__).parent.parent
_version_txt_path = _project_root_path / "version.txt"
_version_py_path = _project_root_path / "pymake" / "config.py"

# file names and the path to the file relative to the repo root directory
file_paths_list = [
    _project_root_path / "README.md",
    _project_root_path / "version.txt",
    _project_root_path / "pymake" / "config.py",
]
file_paths = {pth.name: pth for pth in file_paths_list}  # keys for each file


def split_nonnumeric(s):
    match = re.compile("[^0-9]").search(s)
    return [s[: match.start()], s[match.start() :]] if match else s


_current_version = Version(_version_txt_path.read_text().strip())


def update_version_txt(version: Version) -> None:
    """Update version number in version.txt

    Parameters
    ----------
    version : Version
        version number
    """
    with open(_version_txt_path, "w", encoding="utf8") as f:
        f.write(str(version))
    print(f"Updated {_version_txt_path} to version {version}")


def update_version_py(timestamp: datetime, version: Version) -> None:
    """Update version number in config.py

    Parameters
    ----------
    timestamp : datetime
        current datetime
    version : Version
        version number
    """
    lines = file_paths["config.py"].read_text().rstrip().split("\n")

    with open(_version_py_path, "w", encoding="utf8") as f:
        for line in lines:
            if "__date__" in line:
                line = f'__date__ = "{timestamp:%B %d, %Y}"'
            elif "__version__" in line:
                line = f'__version__ = "{version}"'
            f.write(f"{line}\n")
    print(f"Updated {_version_py_path} to version {version}")


def update_readme_markdown(version: Version) -> None:
    """Update README.md

    Parameters
    ----------
    version : Version
        version number
    """
    fpth = file_paths["README.md"]

    # read README.md into memory
    lines = fpth.read_text().rstrip().split("\n")

    # rewrite README.md
    terminate = False
    with open(fpth, "w", encoding="utf8") as f:
        for line in lines:
            if "### Version " in line:
                line = f"### Version {version}"
            f.write(f"{line}\n")
            if terminate:
                break

    print(f"Updated {fpth} to version {version}")


def update_version(
    timestamp: datetime = datetime.now(),
    version: Version = None,
) -> None:
    """Main function for updating all of the files containing
       version information

    Parameters
    ----------
    timestamp : datetime, optional
        datetime object, by default datetime.now()
    version : Version, optional
        version number, by default None
    """
    lock_path = Path(_version_txt_path.name + ".lock")
    try:
        lock = FileLock(lock_path)
        previous = Version(_version_txt_path.read_text().strip())
        version = (
            version
            if version
            else Version(previous.major, previous.minor, previous.micro)
        )

        with lock:
            update_version_txt(version)
            update_version_py(timestamp, version)
            update_readme_markdown(version)
    finally:
        try:
            lock_path.unlink()
        except:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog=f"Update {_project_name} version",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(_epilog),
    )
    parser.add_argument(
        "-v",
        "--version",
        required=False,
        help="Specify the release version",
    )
    parser.add_argument(
        "-g",
        "--get",
        required=False,
        action="store_true",
        help="Just get the current version number, "
        + "no updates (defaults false)",
    )
    args = parser.parse_args()

    if args.get:
        print(_current_version)
    else:
        update_version(
            timestamp=datetime.now(),
            version=(
                Version(args.version) if args.version else _current_version
            ),
        )
