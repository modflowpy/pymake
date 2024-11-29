#!/usr/bin/env python3
"""Download and build USGS MODFLOW and related programs.

This script originates from pymake: https://github.com/modflowpy/pymake
It requires Python 3.6 or later, and has no dependencies.
"""

import sys
from pathlib import Path
from textwrap import dedent

from pymake.pymake_base import main as pymake_main
from pymake.pymake_parser import parser

__all__ = ["main"]
__license__ = "CC0"


def main() -> None:
    """mfpymake command line interface

    Returns
    -------
    None

    """
    # Show meaningful examples at bottom of help
    prog = Path(sys.argv[0]).stem
    examples = dedent(f"""\
        Examples:

        Compile MODFLOW 6 from the root directory containing the
        source files in subdirectories in the src/ subdirectory:

        $ {prog} src/ mf6 --subdirs

        Compile MODFLOW 6 in the bin subdirectory using the Intel
        Fortran compiler from the root directory containing the source
        files in subdirectories in the the src/ subdirectory:

        $ {prog} src/ mf6 --subdirs -fc ifort --appdir bin
        """)

    # get the arguments
    args = parser(examples=examples)

    # run pymake main
    try:
        pymake_main(
            args.srcdir,
            args.target,
            fc=args.fc,
            cc=args.cc,
            makeclean=args.makeclean,
            expedite=args.expedite,
            dryrun=args.dryrun,
            double=args.double,
            debug=args.debug,
            include_subdirs=args.subdirs,
            fflags=args.fflags,
            cflags=args.cflags,
            arch=args.arch,
            makefile=args.makefile,
            srcdir2=args.commonsrc,
            extrafiles=args.extrafiles,
            excludefiles=args.excludefiles,
            sharedobject=args.sharedobject,
            appdir=args.appdir,
            verbose=args.verbose,
            inplace=args.inplace,
            networkx=args.networkx,
            meson=args.meson,
            mesondir=args.mesondir,
        )
    except (EOFError, KeyboardInterrupt):
        sys.exit(f" cancelling '{sys.argv[0]}'")


if __name__ == "__main__":
    main()
