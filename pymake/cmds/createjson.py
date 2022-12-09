#!/usr/bin/env python3
"""Create pymake code.json file.

This script originates from pymake: https://github.com/modflowpy/pymake
It requires Python 3.6 or later, and has no dependencies.
"""
import sys
from pathlib import Path

from pymake import usgs_program_data
from pymake.pymake_parser import _parser_setup

__all__ = ["main"]
__license__ = "CC0"


def main() -> None:
    """Command line interface

    Returns
    -------
    None

    """
    import argparse

    # Show meaningful examples at bottom of help
    prog = Path(sys.argv[0]).stem
    examples = f"""\
Examples:

  Create code.json in the current directory:
    $ {prog} 

  Create code.json in the ./temp subdirectory:
    $ {prog} -f temp/code.json
    """

    parser_obj = argparse.ArgumentParser(
        description=__doc__.split("\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=examples,
    )

    # command line arguments specific to make-program
    parser_dict = {
        "fpth": {
            "tag": (
                "-f",
                "--fpth",
            ),
            "help": "Path for the json file to be created. "
            + 'Default is "code.json".',
            "default": "code.json",
            "choices": None,
            "action": None,
        },
        "prog_data": {
            "tag": ("--prog_data",),
            "help": "User-specified program database. If prog_data is None, "
            + "it will be created from the USGS program database."
            + "Default is None.",
            "default": None,
            "choices": None,
            "action": None,
        },
        "current": {
            "tag": ("--current",),
            "help": "If False, all USGS program targets are listed. "
            + "If True, only USGS program targets that are "
            + " defined as current are listed. Default is True.",
            "default": True,
            "choices": None,
            "action": "store_true",
        },
        "update": {
            "tag": (
                "-u",
                "--update",
            ),
            "help": "If True, existing targets in the user-specified "
            + "program database with values in the USGS "
            + "program database. If False, existing targets "
            + "in the user-specified program database "
            + "will not be updated. Default is True.",
            "default": True,
            "choices": None,
            "action": "store_true",
        },
        "write_markdown": {
            "tag": ("--write_markdown",),
            "help": "If True, write markdown file that includes the "
            + "target name, version, and the last-modified date of "
            + "the download asset (url). Default is True.",
            "default": True,
            "choices": None,
            "action": "store_true",
        },
        "verbose": {
            "tag": (
                "-v",
                "--verbose",
            ),
            "help": "boolean for verbose output to terminal. Default is True.",
            "default": False,
            "choices": None,
            "action": "store_true",
        },
    }

    # setup parser for make-code-json
    for _, value in parser_dict.items():
        my_parser = _parser_setup(parser_obj, value)
    parser_args = my_parser.parse_args()

    # define args
    args = vars(parser_args)

    # run build_apps
    try:
        usgs_program_data.export_json(**args)
    except (EOFError, KeyboardInterrupt):
        sys.exit(f" cancelling '{sys.argv[0]}'")


if __name__ == "__main__":
    main()
