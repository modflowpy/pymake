# __main__.py
from .pymake_base import main
from .pymake_parser import parser

# get the arguments
args = parser()

# call main -- note that this form allows main to be called
# from python as a function.
main(
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
)
