"""Make a binary executable for a FORTRAN program, such as MODFLOW."""
__author__ = "Christian D. Langevin"
__date__ = "October 26, 2014"
__version__ = "1.1.0"
__maintainer__ = "Christian D. Langevin"
__email__ = "langevin@usgs.gov"
__status__ = "Production"
__description__ = """
This is the pymake program for compiling fortran source files, such as
the source files that come with MODFLOW. The program works by building
a directed acyclic graph of the module dependencies and then compiling
the source files in the proper order.
"""

import os
import sys
import time
import shutil
import argparse

from .compiler_switches import (
    get_osname,
    get_optlevel,
    get_fortran_flags,
    get_c_flags,
    get_linker_flags,
)
from .download import download_and_unzip, zip_all
from .pymake_base import main, parser, get_arg_dict, parser_setup
from .usgsprograms import usgs_program_data
from .usgs_src_update import build_replace


class Pymake:
    """
    Pymake class for interacting with pymake functionality. This is essentially
    a wrapper for all of the pymake functions needed to download and build
    a target.

    """

    def __init__(self, name="pymake", verbose=None):
        self.name = name
        self.url = None
        self.download = None
        self.download_path = None
        self.download_dir = None
        self.srcdir = None
        self.returncode = 0
        self.build_targets = []

        # set class variables with default values from arg_dict
        for key, value in get_arg_dict().items():
            setattr(self, key, value["default"])

        # do not parse command line arguments if program running script is
        # nosetests, pytest, etc.
        if "test" not in sys.argv[0].lower():
            self.arg_parser()

        # reset select variables using passed variables
        if verbose is not None:
            self.verbose = verbose

    def print_settings(self):
        """Print settings defined by command line arguments

        Returns
        -------

        """
        print("\nPymake settings\n" + 30 * "-")
        for key, value in get_arg_dict().items():
            print(" {}={}".format(key, getattr(self, key, value["default"])))
        print("\n")

    def argv_reset_settings(self, args):
        """Reset setting using command line arguments

        Returns
        -------

        """
        for key in args.__dict__:
            if args.__dict__[key] is not None:
                setattr(self, key, args.__dict__[key])
        return

    def arg_parser(self):
        """Setup argparse object for Pymake object using only optional
        command lone arguments.

        Returns
        -------

        """
        loc_dict = get_arg_dict()
        parser = argparse.ArgumentParser(description=__description__,)
        for _, value in loc_dict.items():
            tag = value["tag"][0]
            # only process optional command line variables
            if tag.startswith("-"):
                parser = parser_setup(parser, value, reset_default=True)

        # reset self.variables using optional command line arguments
        self.argv_reset_settings(parser.parse_args())

        return

    def compress_targets(self):
        """Compress targets in build_targets

        Returns
        -------

        """
        zip_pth = self.zip
        if zip_pth is not None:
            targets = []
            bindir = None
            for target in self.build_targets:
                if bindir is None:
                    bindir = os.path.dirname(target)
                targets.append(os.path.basename(target))

            # add code.json
            if "code.json" not in targets:
                targets.append("code.json")

            # delete the zip file if it exists
            if os.path.exists(zip_pth):
                if self.verbose:
                    msg = "Deleting existing zipfile '{}'".format(zip_pth)
                    print(msg)
                os.remove(zip_pth)

            # compress the compiled executables
            if self.verbose:
                msg = "Compressing files in '{}' ".format(
                    bindir
                ) + "directory to zip file '{}'".format(zip_pth)
                print(msg)
            if not zip_all(zip_pth, dir_pths=bindir, patterns=targets):
                self.returncode = 1

        return

    def clean_targets(self):
        """Clean up list of targets

        Returns
        -------

        """
        for target in self.build_targets:
            if os.path.exists(target):
                msg = "removing '{}'".format(target)
                os.remove(target)
            else:
                msg = "'{}' does not exist".format(target)
            if self.verbose:
                print(msg)

        # reset build_targets
        self.build_targets = []

        return

    def download_setup(
        self, target, url=None, download_path=".", verify=True, timeout=30
    ):
        """Setup download

        Parameters
        ----------
        target : str
            target name
        url : str
            url of asset
        download_path : str
            path where the asset will be saved
        verify : bool
            boolean defining ssl verification
        timeout : int
            download timeout in seconds (default is 30)

        Returns
        -------

        """
        # setup program(s) dictionary
        prog_dict = usgs_program_data.get_target(target)

        # set url
        if url is None:
            url = prog_dict.url
        self.url = url

        # set download_dir
        self.download_path = download_path
        self.download_dir = os.path.join(download_path, prog_dict.dirname)

        # set download parameters
        self.download = False
        self.verify = verify
        self.timeout = timeout

        return

    def download_target(
        self, target, url=None, download_path=".", verify=True, timeout=30
    ):
        """Setup and download url

        Parameters
        ----------
        target : str
            target name
        url : str
            url of asset
        download_path : str
            path where the asset will be saved
        verify : bool
            boolean defining ssl verification
        timeout : int
            download timeout in seconds (default is 30)

        Returns
        -------
        success : bool
            boolean flag indicating download success

        """
        # setup the download
        self.download_setup(
            target,
            url=url,
            download_path=download_path,
            verify=verify,
            timeout=timeout,
        )

        return self.download_url()

    def download_url(self):
        """Download files from the url

        Returns
        -------
        success : bool
            boolean flag indicating download success

        """
        if not self.download:
            # write message
            msg = "downloading...'{}'".format(self.url)
            print(msg)

            # download the url
            self.download = download_and_unzip(
                self.url,
                pth=self.download_path,
                verify=self.verify,
                timeout=self.timeout,
                verbose=self.verbose,
            )
        return self.download

    def download_cleanup(self):
        """

        Returns
        -------

        """
        if self.download is not None:
            if self.download:
                # write process information
                msg = "cleaning temporary files in...'{}'".format(
                    self.download_dir
                )
                print(msg)

                # reset self.download
                self.download = None

                if os.path.exists(self.download_dir):
                    ntries = 10
                    for itries in range(ntries):
                        # wait to delete on windows
                        if get_osname() == "win32":
                            time.sleep(3)

                        # remove the directory
                        try:
                            shutil.rmtree(self.download_dir)
                            if self.verbose:
                                print(
                                    "removing download "
                                    + "directory...'{}'".format(
                                        self.download_dir
                                    )
                                )
                            break
                        except:
                            if self.verbose:
                                msg = "    removal attempt {:>2d} ".format(
                                    itries + 1
                                )
                                msg += "of {:>2d}".format(ntries)
                                print(msg)

                    # wait prior to returning on windows
                    if get_osname() == "win32":
                        time.sleep(6)

        return

    def set_include_subdirs(self):
        """Determine if sub-directories in the source directory should be
        included.

        Parameters
        ----------

        Returns
        -------

        """
        # strip .exe extension if necessary
        target = os.path.basename(self.target)
        if ".exe" in target.lower():
            target = target[:-4]

        # determine if source subdirectories should be included
        if target in ["mf6", "gridgen", "mf6beta", "gsflow"]:
            self.include_subdirs = True

        return

    def set_build_target_bool(self, target=None):
        """Evaluate if the executable exists and if so and the command line
        argument --keep is specified then the executable is not built.

        Parameters
        ----------

        Returns
        -------
        build : bool
            boolean indicating if the executable should be built

        """
        if target is None:
            target = self.target

        if self.appdir is not None:
            if os.path.dirname(self.target) != self.appdir:
                target = os.path.join(self.appdir, os.path.basename(target))

        build_target = True
        if os.path.exists(target):
            if self.keep:
                build_target = False

        return build_target

    def set_extrafiles(self):
        """Set extrafiles to compile target. Default is None.

        Parameters
        ----------
        target : str
            target to build
        download_dir : str
            path downloaded files will be placed in

        Returns
        -------

        """
        extrafiles = self.extrafiles
        if extrafiles is None:
            if self.target in ("zbud6",):
                extrafiles = [
                    "../../../src/Utilities/ArrayHandlers.f90",
                    "../../../src/Utilities/ArrayReaders.f90",
                    "../../../src/Utilities/BlockParser.f90",
                    "../../../src/Utilities/Budget.f90",
                    "../../../src/Utilities/Constants.f90",
                    "../../../src/Utilities/compilerversion.fpp",
                    "../../../src/Utilities/genericutils.f90",
                    "../../../src/Utilities/InputOutput.f90",
                    "../../../src/Utilities/kind.f90",
                    "../../../src/Utilities/OpenSpec.f90",
                    "../../../src/Utilities/sort.f90",
                    "../../../src/Utilities/Message.f90",
                    "../../../src/Utilities/defmacro.fpp",
                    "../../../src/Utilities/Sim.f90",
                    "../../../src/Utilities/SimVariables.f90",
                    "../../../src/Utilities/version.f90",
                ]

            # evaluate extrafiles type
            if extrafiles:
                srcdir = os.path.abspath(self.srcdir)
                if isinstance(extrafiles, list):
                    for idx, value in enumerate(extrafiles):
                        fpth = os.path.join(srcdir, value)
                        extrafiles[idx] = os.path.normpath(fpth)
                elif isinstance(extrafiles, str):
                    fpth = os.path.join(srcdir, extrafiles)
                    extrafiles = os.path.normpath(fpth)
                else:
                    msg = (
                        "invalid extrafiles format - "
                        + "must be a list or string"
                    )
                    raise ValueError(msg)

                # reset extrafiles
                self.extrafiles = extrafiles

        return

    def build(self, target=None, srcdir=None, modify_exe_name=False):
        """Build the target

        Parameters
        ----------
        target : str
        srcdir : str
            path to directory with source files
        modify_exe_name : bool
            boolean that determines

        Returns
        -------

        """
        if target is not None:
            self.target = target
            self.srcdir = None

        if srcdir is not None:
            self.srcdir = srcdir

        prog_dict = usgs_program_data.get_target(self.target)
        if self.srcdir is None:
            self.srcdir = os.path.join(self.download_dir, prog_dict.srcdir)

        # set include_subdirs for known targets
        self.set_include_subdirs()

        # set extrafiles for known targets
        self.set_extrafiles()

        # set compiler flags
        if self.fc != "none":
            if self.fflags is None:
                optlevel = (
                    get_optlevel(
                        self.target, self.fc, self.cc, self.debug, [], []
                    )
                    + " "
                )

                self.fflags = optlevel + " ".join(
                    get_fortran_flags(
                        self.target,
                        self.fc,
                        [],
                        self.debug,
                        self.double,
                        self.sharedobject,
                    )
                )
        if self.cc != "none":
            if self.cflags is None:
                optlevel = (
                    get_optlevel(
                        self.target, self.fc, self.cc, self.debug, [], []
                    )
                    + " "
                )

                self.cflags = optlevel + " ".join(
                    get_c_flags(
                        self.target,
                        self.cc,
                        [],
                        self.debug,
                        sharedobject=self.sharedobject,
                    )
                )
        if self.syslibs is None:
            self.syslibs = " ".join(
                get_linker_flags(
                    self.target,
                    self.fc,
                    self.cc,
                    [],
                    [],
                    sharedobject=self.sharedobject,
                )[1]
            )

        self.target = self.update_target(
            self.target, modify_target=modify_exe_name
        )

        build_target = self.set_build_target_bool()

        if build_target:
            # print Pymake() settings
            if self.verbose:
                self.print_settings()

            # download url if it has not been downloaded
            if self.download is not None:
                self.download_url()

            # update source code, if necessary
            replace_function = build_replace(self.target)
            if replace_function is not None:
                if self.verbose:
                    msg = "replacing select source files for " + "{}\n".format(
                        self.target
                    )
                    print(msg)

                # execute select replace function
                replace_function(
                    self.srcdir, self.fc, self.cc, self.arch, self.double,
                )

            # write message
            print("compiling...{}".format(self.target))

            # build the target
            self.returncode = main(
                srcdir=self.srcdir,
                target=self.target,
                fc=self.fc,
                cc=self.cc,
                makeclean=self.makeclean,
                expedite=self.expedite,
                dryrun=self.dryrun,
                double=self.double,
                debug=self.debug,
                include_subdirs=self.include_subdirs,
                fflags=self.fflags,
                cflags=self.cflags,
                syslibs=self.syslibs,
                arch=self.arch,
                makefile=self.makefile,
                srcdir2=self.srcdir2,
                extrafiles=self.extrafiles,
                excludefiles=self.excludefiles,
                sharedobject=self.sharedobject,
                appdir=self.appdir,
            )

        # issue error if target was not built
        if self.returncode != 0:
            raise FileNotFoundError("could not build {}".format(self.target))
        # add target to list of targets
        else:
            if os.path.abspath(self.target) not in self.build_targets:
                self.build_targets.append(os.path.abspath(self.target))

        return self.returncode

    def update_target(self, target, modify_target=False):
        """Update target name with executable extension on Windows and
        based on pymake settings.

        Parameters
        ----------
        target : str
            target name
        modify_target : bool
            boolean indicating if the target name can be modified based
            on pymake double and debug settings (default is False)

        Returns
        -------
        target : str
            updated target name

        """
        # add exe extension to target on windows
        if sys.platform.lower() == "win32":
            filename, file_extension = os.path.splitext(target)
            if file_extension.lower() != ".exe":
                target += ".exe"

        # add double and debug to target name
        if modify_target:
            if self.double:
                filename, file_extension = os.path.splitext(target)
                if "dbl" not in filename.lower():
                    target = filename + "dbl" + file_extension
            if self.debug:
                filename, file_extension = os.path.splitext(target)
                if filename.lower()[-1] != "d":
                    target = filename + "d" + file_extension
        return target


if __name__ == "__main__":
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
    )
