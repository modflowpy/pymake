#!/usr/bin/env python3
"""Download and build USGS MODFLOW and related programs.

This script originates from pymake: https://github.com/modflowpy/pymake
It requires Python 3.6 or later, and has no dependencies.
"""

import sys
from pathlib import Path

from pymake import build_apps, usgs_program_data
from pymake.pymake_parser import _get_standard_arg_dict, _parser_setup

__all__ = ["main"]
__license__ = "CC0"

DICT_KEYS = (
    "targets",
    "appdir",
    "verbose",
    "fc",
    "cc",
    "fflags",
    "cflags",
    "double",
    "verbose",
    "zip",
    "keep",
    "dryrun",
    "meson",
)

# command arguments (sys.argv) to pop from ARGS
COM_ARG_KEYS = (
    "fc",
    "cc",
    "fflags",
    "cflags",
    "double",
    "zip",
    "keep",
    "dryrun",
)

# ARGS to keep and pass to build_apps()
KEEP_ARG_KEYS = ("double",)


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

  Download and compile MODFLOW 6 in the current directory:
    $ {prog} mf6

  Download and compile triangle in the ./temp subdirectory:
    $ {prog} triangle --appdir temp

  Download and compile double precision versions of mf2005 and mfusg 
    $ {prog} mf2005,mfusg --double

  Download and compile all programs in the ./temp subdirectory:
    $ {prog} : --appdir temp
    """

    parser_obj = argparse.ArgumentParser(
        description=__doc__.split("\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=examples,
    )
    all_targets = sorted(usgs_program_data.get_keys(current=True))
    all_targets.append(":")
    targets_help = (
        "Program(s) to build. Options:\n  "
        + ", ".join(all_targets)
        + ". Specifying the target to be ':' will "
        + "build all of the programs. Multiple targets can be specified "
        + "by separating individual targets by a comma (i.e., mf6,zbud6)."
    )

    # command line arguments specific to make-program
    parser_dict = {
        "targets": {
            "tag": ("targets",),
            "help": targets_help,
            "default": None,
            "choices": None,
            "action": None,
        },
    }

    # add standard command line arguments to parser dictionary for make-program
    for key, value in _get_standard_arg_dict().items():
        if key in DICT_KEYS:
            parser_dict[key] = value

    # setup parser for make-program
    for _, value in parser_dict.items():
        my_parser = _parser_setup(parser_obj, value)
    parser_args = my_parser.parse_args()

    # define args
    args = vars(parser_args)

    # filter parser arguments into args and command line arguments
    # com_arg_var = {}
    arg_key_pop = []
    com_arg_pop = []
    for key, arg in args.items():
        if key in COM_ARG_KEYS:
            # com_arg_var[key] = arg
            arg_key_pop.append(key)
        else:
            for carg in sys.argv:
                if key in carg:
                    com_arg_pop.append(carg)
                    if arg in sys.argv:
                        com_arg_pop.append(arg)

    # add --targets value to com_arg_pop
    com_arg_pop.append(args["targets"])

    # delete arguments that are used by Pymake() class in build_apps
    for key in arg_key_pop:
        if key not in KEEP_ARG_KEYS:
            del args[key]

    # remove args from command line arguments
    for key in com_arg_pop:
        sys.argv.remove(key)

    # run build_apps
    try:
        build_apps(**args)
    except (EOFError, KeyboardInterrupt):
        sys.exit(f" cancelling '{sys.argv[0]}'")


if __name__ == "__main__":
    main()
