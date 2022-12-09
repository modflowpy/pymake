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
    "release_precision",
    "fc",
    "cc",
    "fflags",
    "cflags",
    "verbose",
    "zip",
    "keep",
    "dryrun",
)
COM_ARG_KEYS = ("fc", "cc", "fflags", "cflags", "zip", "keep", "dryrun")


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
        + "build all of the programs."
    )

    release_precision_help = (
        "If release_precision is False, then the "
        + "release precision version will be compiled "
        + "along with a double precision version of "
        + "the program for programs where the standard_"
        + "switch and double_switch in "
        + "usgsprograms.txt is True. default is True."
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
        "release_precision": {
            "tag": ("--release_precision",),
            "help": release_precision_help,
            "default": False,
            "choices": None,
            "action": "store_true",
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
