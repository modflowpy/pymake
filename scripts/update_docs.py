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

# the width the help is rendered at, so that the output does not depend on
# the terminal the script is run in
COLUMNS = "100"

ROOT = Path(__file__).parent.parent


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
    if prog == "mfpymake":
        from pymake.cmds.mfpymakecli import examples
        from pymake.pymake_parser import build_parser

        parser_obj = build_parser(examples=examples(prog), prog=prog)
    elif prog == "make-program":
        from pymake.cmds.build import build_parser

        parser_obj = build_parser(prog=prog)
    else:
        raise ValueError(f"unknown program ({prog})")

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


def _replace_block(text, fence, help_text):
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
            if line.startswith("usage: "):
                start = idx
        elif line.rstrip() == "```":
            return "".join(lines[:start]) + help_text + "\n" + "".join(lines[idx:])
    raise ValueError(f"no block opened by {fence} with a usage message was found")


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
        after = _replace_block(before, fence, _help_text(prog))
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
