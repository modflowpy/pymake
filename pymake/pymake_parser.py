"""Parser used to process command line arguments when running pymake directly
from the command line or in a script. The standard argparse module is used
to parse command line arguments. Available command line arguments are
programmatically developed by a protected dictionary. The parser can be
accessed using:

.. code-block:: python

    import pymake
    args = pymake.parser()


"""

import argparse
from .config import __description__


def _get_arg_dict():
    """Get command line argument dictionary

    Returns
    -------
    return : dict
        Dictionary of command line argument options

    """
    return {
        "srcdir": {
            "tag": ("srcdir",),
            "help": "Path source directory.",
            "default": None,
            "choices": None,
            "action": None,
        },
        "target": {
            "tag": ("target",),
            "help": "Name of target to create. (can include path)",
            "default": None,
            "choices": None,
            "action": None,
        },
        "fc": {
            "tag": ("-fc",),
            "help": "Fortran compiler to use. (default is gfortran)",
            "default": "gfortran",
            "choices": ["ifort", "mpiifort", "gfortran", "none"],
            "action": None,
        },
        "cc": {
            "tag": ("-cc",),
            "help": "C/C++ compiler to use. (default is gcc)",
            "default": "gcc",
            "choices": [
                "gcc",
                "clang",
                "clang++",
                "icc",
                "icl",
                "mpiicc",
                "g++",
                "cl",
                "none",
            ],
            "action": None,
        },
        "arch": {
            "tag": ("-ar", "--arch"),
            "help": """Architecture to use for Intel and Microsoft
                         compilers on Windows. (default is intel64)""",
            "default": "intel64",
            "choices": ["ia32", "ia32_intel64", "intel64"],
            "action": None,
        },
        "makeclean": {
            "tag": ("-mc", "--makeclean"),
            "help": """Clean temporary object, module, and source files when
                         done. (default is False)""",
            "default": False,
            "choices": None,
            "action": "store_true",
        },
        "double": {
            "tag": ("-dbl", "--double"),
            "help": "Force double precision. (default is False)",
            "default": False,
            "choices": None,
            "action": "store_true",
        },
        "debug": {
            "tag": ("-dbg", "--debug"),
            "help": "Create debug version. (default is False)",
            "default": False,
            "choices": None,
            "action": "store_true",
        },
        "expedite": {
            "tag": ("-e", "--expedite"),
            "help": """Only compile out of date source files.
                         Clean must not have been used on previous build.
                         (default is False)""",
            "default": False,
            "choices": None,
            "action": "store_true",
        },
        "dryrun": {
            "tag": ("-dr", "--dryrun"),
            "help": """Do not actually compile.  Files will be
                         deleted, if --makeclean is used.
                         Does not work yet for ifort. (default is False)""",
            "default": False,
            "choices": None,
            "action": "store_true",
        },
        "include_subdirs": {
            "tag": ("-sd", "--subdirs"),
            "help": """Include source files in srcdir subdirectories.
                         (default is None)""",
            "default": None,
            "choices": None,
            "action": "store_true",
        },
        "fflags": {
            "tag": ("-ff", "--fflags"),
            "help": """Additional Fortran compiler flags. Fortran compiler
                         flags should be enclosed in quotes and start with a
                         blank space or separated from the name (-ff or
                         --fflags) with a equal sign (-ff='-O3').
                         (default is None)""",
            "default": None,
            "choices": None,
            "action": None,
        },
        "cflags": {
            "tag": ("-cf", "--cflags"),
            "help": """Additional C/C++ compiler flags. C/C++ compiler
                         flags should be enclosed in quotes and start with a
                         blank space or separated from the name (-cf or
                         --cflags) with a equal sign (-cf='-O3').
                         (default is None)""",
            "default": None,
            "choices": None,
            "action": None,
        },
        "syslibs": {
            "tag": ("-sl", "--syslibs"),
            "help": """Linker system libraries. Linker libraries should be
                         enclosed in quotes and start with a blank space or 
                         separated from the name (-sl or --syslibs) with a
                         equal sign (-sl='-libgcc'). (default is None)""",
            "default": None,
            "choices": ["-lc", "-lm"],
            "action": None,
        },
        "makefile": {
            "tag": ("-mf", "--makefile"),
            "help": "Create a GNU make makefile. (default is False)",
            "default": False,
            "choices": None,
            "action": "store_true",
        },
        "srcdir2": {
            "tag": ("-cs", "--commonsrc"),
            "help": """Additional directory with common source files.
                         (default is None)""",
            "default": None,
            "choices": None,
            "action": None,
        },
        "extrafiles": {
            "tag": ("-ef", "--extrafiles"),
            "help": """List of extra source files to include in the
                         compilation. extrafiles can be either a list of files
                         or the name of a text file that contains a list of
                         files. (default is None)""",
            "default": None,
            "choices": None,
            "action": None,
        },
        "excludefiles": {
            "tag": ("-exf", "--excludefiles"),
            "help": """List of extra source files to exclude from the
                         compilation. excludefiles can be either a list of
                         files or the name of a text file that contains a list
                         of files. (default is None)""",
            "default": None,
            "choices": None,
            "action": None,
        },
        "sharedobject": {
            "tag": ("-so", "--sharedobject"),
            "help": """Create shared object or dll on Windows.
                         (default is False)""",
            "default": False,
            "choices": None,
            "action": "store_true",
        },
        "appdir": {
            "tag": ("-ad", "--appdir"),
            "help": """Target path that overides path defined target
                         path (default is None)""",
            "default": None,
            "choices": None,
            "action": None,
        },
        "verbose": {
            "tag": ("-v", "--verbose"),
            "help": "Verbose output to terminal. (default is False)",
            "default": False,
            "choices": None,
            "action": "store_true",
        },
        "keep": {
            "tag": ("--keep",),
            "help": "Keep existing executable. (default is False)",
            "default": False,
            "choices": None,
            "action": "store_true",
        },
        "zip": {
            "tag": ("--zip",),
            "help": "Zip built executable. (default is False)",
            "default": None,
            "choices": None,
            "action": None,
        },
        "inplace": {
            "tag": ("--inplace",),
            "help": """Source files in srcdir are used directly.
                         (default is False)""",
            "default": False,
            "choices": None,
            "action": "store_true",
        },
        "networkx": {
            "tag": ("--networkx",),
            "help": """Use networkx package to build Directed Acyclic Graph
                     use to determine the order source files are compiled
                     in. (default is False)""",
            "default": False,
            "choices": None,
            "action": "store_true",
        },
    }


def _parser_setup(parser_obj, value, reset_default=False):
    """Add argument to argparse object

    Parameters
    ----------
    parser_obj : object
        argparse object
    value : dict
        argparse settings
    reset_default : bool
        boolean that defines if default values should be used

    Returns
    -------
    parser_obj : object
        updated argparse object

    """
    if reset_default:
        default = None
    else:
        default = value["default"]
    if value["action"] is None:
        parser_obj.add_argument(
            *value["tag"],
            help=value["help"],
            default=default,
            choices=value["choices"],
        )
    else:
        parser_obj.add_argument(
            *value["tag"],
            help=value["help"],
            default=default,
            action=value["action"],
        )
    return parser_obj


def parser():
    """Construct the parser and return argument values.

    Parameters
    ----------

    Returns
    -------
    args : Namespace object
        Namespace with command line arguments

    """
    description = __description__
    parser_obj = argparse.ArgumentParser(
        description=description,
        epilog="""Note that the source directory
                                     should not contain any bad or duplicate
                                     source files as all source files in the
                                     source directory, the common source file
                                     directory (srcdir2), and the extra files
                                     (extrafiles) will be built and linked.
                                     Files can be excluded by using the
                                     excludefiles command line switch.""",
    )

    for _, value in _get_arg_dict().items():
        my_parser = _parser_setup(parser_obj, value)
    parser_args = my_parser.parse_args()
    return parser_args
