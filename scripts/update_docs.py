#!/usr/bin/env python3
"""Update the command line help in the documentation.

The usage and option blocks in the README and the docs are the --help output
of a command, which goes stale when an argument is added or changed. This
script writes the current output into each block.

Run with --check to report a block that is out of date without writing it,
which is what the documentation test does.
"""

import argparse
import os
import sys
from pathlib import Path

from pymake.cmds.build import build_parser as make_program_parser
from pymake.cmds.mfpymakecli import examples
from pymake.pymake_base import _openspec_content
from pymake.pymake_parser import build_parser as mfpymake_parser

# the width the help is rendered at, so that the output does not depend on
# the terminal the script is run in
COLUMNS = "100"

ROOT = Path(__file__).parent.parent


def _formatter_class(base):
    """Return a formatter that writes an option the way python 3.13 does.

    Parameters
    ----------
    base : type
        formatter class the parser was built with

    Returns
    -------
    formatter_class : type
        formatter class that does not depend on the python version

    """

    class Formatter(base):
        def _format_action_invocation(self, action):
            # python 3.13 stopped repeating the metavar for every option
            # string, and the newer form is written on older pythons too
            if not action.option_strings:
                return super()._format_action_invocation(action)
            if action.nargs == 0:
                return ", ".join(action.option_strings)
            default = self._get_default_metavar_for_optional(action)
            args_string = self._format_args(action, default)
            return ", ".join(action.option_strings) + " " + args_string

    return Formatter


def _blocks():
    """Return the documentation blocks and the command each one shows.

    Returns
    -------
    blocks : list of tuple
        path, program name, and fence for each block

    """
    return [
        (ROOT / "README.md", "mfpymake", "```"),
        (ROOT / "docs" / "getting_started.md", "mfpymake", "```"),
        (ROOT / "docs" / "build_apps.md", "make-program", "```console"),
        (ROOT / "README.md", "openspec", "```"),
        (ROOT / "docs" / "getting_started.md", "openspec", "```"),
    ]


def _help_text(prog):
    """Return the --help output for a program.

    Parameters
    ----------
    prog : str
        console script name

    Returns
    -------
    help_text : str
        help output for the program

    """
    if prog == "openspec":
        return _openspec_content().rstrip()

    if prog == "mfpymake":
        parser_obj = mfpymake_parser(examples=examples(prog), prog=prog)
    elif prog == "make-program":
        parser_obj = make_program_parser(prog=prog)
    else:
        raise ValueError(f"unknown program ({prog})")

    parser_obj.formatter_class = _formatter_class(parser_obj.formatter_class)

    # argparse wraps to the terminal width, so it is fixed here and the
    # environment is put back so that the width is not changed for a caller
    columns = os.environ.get("COLUMNS")
    os.environ["COLUMNS"] = COLUMNS
    try:
        return parser_obj.format_help().rstrip()
    finally:
        if columns is None:
            del os.environ["COLUMNS"]
        else:
            os.environ["COLUMNS"] = columns


def _replace_block(text, fence, help_text, marker="usage: "):
    """Replace the fenced block that holds the help output.

    Parameters
    ----------
    text : str
        contents of the documentation file
    fence : str
        fence that opens the block
    help_text : str
        help output to write into the block

    Returns
    -------
    updated : str
        contents with the block replaced

    """
    lines = text.splitlines(keepends=True)
    in_block = False
    start = None
    for idx, line in enumerate(lines):
        if not in_block:
            in_block = line.rstrip() == fence
        elif start is None:
            # a line the block opens with, such as the command that was run,
            # is kept
            if line.startswith(marker):
                start = idx
        elif line.rstrip() == "```":
            return "".join(lines[:start]) + help_text + "\n" + "".join(lines[idx:])
    raise ValueError(f"no block opened by {fence} starting with {marker!r} was found")


def _updated(path, prog, fence):
    """Return the contents of a documentation file with its block written.

    Parameters
    ----------
    path : Path
        path to the documentation file
    prog : str
        what the block shows
    fence : str
        fence that opens the block

    Returns
    -------
    updated : str
        contents with the block written

    """
    marker = "c -- created by" if prog == "openspec" else "usage: "
    return _replace_block(path.read_text(), fence, _help_text(prog), marker=marker)


def main():
    """Update or check the command line help in the documentation."""
    arg_parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    arg_parser.add_argument(
        "--check",
        action="store_true",
        help="report a block that is out of date instead of writing it",
    )
    args = arg_parser.parse_args()

    stale = []
    for path, prog, fence in _blocks():
        before = path.read_text()
        after = _updated(path, prog, fence)
        name = path.relative_to(ROOT)
        if before == after:
            print(f"  {name} current ({prog})")
            continue
        stale.append(str(name))
        if args.check:
            print(f"  {name} out of date ({prog})")
        else:
            path.write_text(after)
            print(f"  {name} updated ({prog})")

    if not stale:
        print("\nthe documented command line help is up to date")
        return 0
    if args.check:
        print(
            f"\n{len(stale)} block(s) out of date, "
            "run 'pixi run update-docs' to write them"
        )
        return 1
    print(f"\nupdated {len(stale)} block(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
