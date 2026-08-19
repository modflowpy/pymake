""":code:`Pymake()` class to make a binary executable for a FORTRAN, C, or C++
program, such as MODFLOW 6.

An example of how to build MODFLOW-2005 from source files in the official
release downloaded from the USGS using Intel compilers is:

.. code-block:: python

    import pymake

    # create an instance of the Pymake object
    pm = pymake.Pymake(verbose=True)

    # reset select pymake settings
    pm.target = "mf2005"
    pm.appdir = "../bin"
    pm.fc = "ifort"
    pm.cc = "icc"
    pm.fflags = "-O3 -fbacktrace"
    pm.cflags = "-O3"

    # download the target
    pm.download_target(pm.target, download_path="temp")

    # build the target
    pm.build()

    # clean up downloaded files
    pm.finalize()

All other settings not specified in the script would be based on command
line arguments or default values. The same :code:`Pymake()` object could be
used to compile MODFLOW 6 by appending the following code to the previous code
block:

.. code-block:: python

    # reset the target
    pm.target = "mf6"

    # download the target
    pm.download_target(pm.target, download_path="temp")

    # build the target
    pm.build()

    # clean up downloaded files
    pm.finalize()

The Intel compilers and fortran flags defined previously would be used when
MODFLOW 6 was built.

"""

import argparse
import os
import shutil
import sys
import time
from pathlib import Path
from zipfile import ZipFile

from .config import __description__
from .pymake_base import main
from .pymake_parser import _get_standard_arg_dict, _parser_setup
from .utils._compiler_switches import (
    _get_osname,
)
from .utils._usgs_src_update import _build_replace
from .utils.download import download_and_unzip, zip_all
from .utils.usgsprograms import usgs_program_data


class Pymake:
    """Pymake class for interacting with pymake functionality. This is essentially
    a wrapper for all of the pymake functions needed to download and build
    a target.

    """

    def __init__(self, name="pymake", verbose=None):
        self.name = name
        self.url = None
        self.download = None
        self.download_path = None
        self.download_dir = None
        self.returncode = 0
        self.build_targets = []

        # initialize class variables available as argv items
        self.target = None
        self.srcdir = None
        self.fc = None
        self.cc = None
        self.makeclean = None
        self.double = None
        self.debug = None
        self.include_subdirs = None
        self.fflags = None
        self.cflags = None
        self.syslibs = None
        self.makefile = None
        self.makefile_only = None
        self.makefiledir = None
        self.srcdir2 = None
        self.extrafiles = None
        self.excludefiles = None
        self.sharedobject = None
        self.appdir = None
        self.keep = None
        self.zip = None
        self.inplace = None
        self.mesondir = None
        # the mesondir pymake set, so that one the user set is not replaced
        self._set_mesondir_value = None

        # set class variables with default values from arg_dict
        for key, value in _get_standard_arg_dict().items():
            setattr(self, key, value["default"])

        # parse command line arguments if python is running script
        if sys.argv[0].lower().endswith(".py") or "make-program" in sys.argv[0].lower():
            self._arg_parser()

        # reset select variables using passed variables
        if verbose is not None:
            self.verbose = verbose

        # reset fortran and c/c++ if fc and cc environmental variables are set
        env_var = os.environ.get("FC")
        if env_var is not None:
            if env_var != self.fc:
                self.fc = env_var
        env_var = os.environ.get("CC")
        if env_var is not None:
            if env_var != self.cc:
                self.cc = env_var

    def reset(self, target):
        """Reset PyMake object variables for a target.

        Parameters
        ----------
        target : str
            target name

        Returns
        -------

        """
        if self.verbose:
            print("resetting Pymake class")
        self.target = target
        self.srcdir = None

    def finalize(self):
        """Finalize Pymake class.

        Returns
        -------

        """
        if self.download:
            self._download_cleanup()

    def _print_settings(self):
        """Print settings defined by command line arguments.

        Returns
        -------

        """
        print("\nPymake settings\n" + 30 * "-")
        for key, value in _get_standard_arg_dict().items():
            print_value = getattr(self, key, value["default"])
            if isinstance(print_value, list):
                print_value = ", ".join(print_value)
            print(f" {key}={print_value}")
        print("\n")

    def argv_reset_settings(self, args):
        """Reset settings using command line arguments.

        Parameters
        ----------
        args : Namespace object
            reset self.variables using command line arguments

        Returns
        -------

        """
        for key in args.__dict__:
            if args.__dict__[key] is not None:
                setattr(self, key, args.__dict__[key])
        return

    def _arg_parser(self):
        """Setup argparse object for Pymake object using only optional
        command line arguments.

        Returns
        -------

        """
        loc_dict = _get_standard_arg_dict()
        parser = argparse.ArgumentParser(description=__description__)
        for _, value in loc_dict.items():
            tag = value["tag"][0]
            # only process optional command line variables
            if tag.startswith("-"):
                parser = _parser_setup(parser, value, reset_default=True)

        # reset self.variables using optional command line arguments
        self.argv_reset_settings(parser.parse_args())

        return

    def compress_targets(self):
        """Compress targets in build_targets list.

        Returns
        -------

        """
        zip_pth = self.zip
        if zip_pth is not None:
            targets = []
            appdir = self.appdir

            # list of applications build at this time
            if len(self.build_targets) > 0:
                for target in self.build_targets:
                    targets.append(Path(target).name)

                    # set appdir based on first target, assumes that the path
                    # for all of the targets are the same
                    if appdir is None:
                        appdir = os.path.dirname(target)
            # determine files in appdir if no applications build at this
            # time (--keep command line argument)
            else:
                if appdir is None:
                    appdir = "."
                for pth in sorted(Path(appdir).iterdir()):
                    targets.append(pth.name)

            # add code.json
            if Path("code.json").exists():
                if "code.json" not in targets:
                    targets.append("code.json")

            # delete the zip file if it exists
            zip_str = str(Path(zip_pth).resolve())
            if Path(zip_pth).exists():
                if self.keep:
                    if self.verbose:
                        print(f"Appending files to existing zipfile '{zip_str}'")
                    with ZipFile(zip_pth, mode="r") as zf:
                        available_file_paths = zf.namelist()
                        pop_list = []
                        for target in targets:
                            for temp_path in available_file_paths:
                                if target == temp_path:
                                    pop_list.append(target)
                                    break
                        for target in pop_list:
                            targets.remove(target)
                else:
                    if self.verbose:
                        print(f"Deleting existing zipfile '{zip_str}'")
                    Path(zip_pth).unlink()

            # print a message describing the zip process
            if self.verbose:
                print(
                    f"Compressing files in '{appdir}' directory to zip file '{zip_str}'"
                )
                for idx, target in enumerate(targets):
                    print(f" {idx + 1:>3d}. adding '{target}' to zipfile")

            # compress the compiled executables
            if not zip_all(
                zip_pth, dir_pths=appdir, patterns=targets, append=self.keep
            ):
                self.returncode = 1

        return

    def _clean_targets(self):
        """Clean up list of targets.

        Returns
        -------

        """
        for target in self.build_targets:
            if Path(target).exists():
                msg = f"removing '{target}'"
                Path(target).unlink()
            else:
                msg = f"'{target}' does not exist"
            if self.verbose:
                print(msg)

        # reset build_targets
        self.build_targets = []

        return

    def download_setup(
        self, target, url=None, download_path=".", verify=True, timeout=30
    ):
        """Setup download.

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

        # determine if the download url has changed
        new_url = False
        if self.url != url:
            new_url = True

        if new_url:
            # automatic clean up
            if self.download:
                self._download_cleanup()

            # setup new
            self.url = url
            self.download = False
            self.verify = verify
            self.timeout = timeout
            self.download_path = download_path
            self.download_dir = str(Path(download_path) / prog_dict.dirname)

        return

    def download_target(
        self, target, url=None, download_path=".", verify=True, timeout=30
    ):
        """Setup and download url.

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
            target, url=url, download_path=download_path, verify=verify, timeout=timeout
        )

        return self.download_url()

    def download_url(self):
        """Download files from the url.

        Returns
        -------
        success : bool
            boolean flag indicating download success

        """
        if not self.download:
            # write message
            msg = f"downloading...'{self.url}'"
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

    def _download_cleanup(self):
        """Remove the temporary download directory.

        Returns
        -------

        """
        if self.download is not None:
            if self.download:
                # write process information
                msg = f"cleaning temporary files in...'{self.download_dir}'"
                print(msg)

                # reset self.download
                self.download = None

                download_dir = Path(self.download_dir)
                if download_dir.is_dir():
                    ntries = 10
                    for itries in range(ntries):
                        # wait to delete on windows
                        if _get_osname() == "win32":
                            time.sleep(3)

                        # remove the directory
                        try:
                            shutil.rmtree(download_dir)
                            if self.verbose:
                                print(f"removing download directory...'{download_dir}'")
                            break
                        except:
                            if self.verbose:
                                msg = (
                                    f"    removal attempt {itries + 1:>2d} "
                                    f"of {ntries:>2d}"
                                )
                                print(msg)

                    # wait prior to returning on windows
                    if _get_osname() == "win32":
                        time.sleep(6)

        return

    def _set_mesondir(self):
        """Set mesondir to the directory a target was downloaded to.

        A meson build reads the build file a target provides, where there is
        one, and writes a generated build file where there is not, so both
        belong with the source. The default is the current directory, which
        two builds of different targets would share. The directory is only
        changed when mesondir is still the default, so that a mesondir set by
        the user is respected.

        Returns
        -------

        """
        # a mesondir pymake set for a target it built before is replaced,
        # since that download directory is removed when the target is done,
        # and a mesondir the user set is respected
        if self.mesondir is not None and self.mesondir != self._set_mesondir_value:
            return

        # the build file belongs with the source, which is the directory a
        # downloaded target was extracted to
        self.mesondir = "." if self.download_dir is None else self.download_dir
        self._set_mesondir_value = self.mesondir
        if self.verbose:
            provided = (Path(self.mesondir) / "meson.build").is_file()
            action = "using" if provided else "writing"
            print(f"{action} the meson build file in...'{self.mesondir}'")

    def _set_include_subdirs(self):
        """Determine if sub-directories in the source directory should be
        included.

        Parameters
        ----------

        Returns
        -------

        """
        # determine if source subdirectories should be included
        if self._get_base_target() in (
            "mf6",
            "libmf6",
            "gridgen",
            "mf6beta",
        ):
            self.include_subdirs = True
        else:
            self.include_subdirs = False

        return

    def set_build_target_bool(self, target=None):
        """Evaluate if the executable exists and if so and the command line
        argument --keep is specified then the executable is not built.

        Parameters
        ----------
        target : str
            target name. If target is None self.target will be used.
            (default is None)

        Returns
        -------
        build : bool
            boolean indicating if the executable should be built

        """
        if target is None:
            target = self.target

        if self.appdir is not None:
            if os.path.dirname(self.target) != self.appdir:
                target = str(Path(self.appdir) / Path(target).name)

        build_target = True
        if Path(target).exists():
            if self.keep:
                build_target = False

        return build_target

    def _get_base_target(self):
        """Get base target name without path and extension.

        Returns
        -------
        target : str
            target name without path and extension

        """
        target = Path(self.target).name
        if target.lower().endswith(".exe"):
            target = target[:-4]
        elif target.lower().endswith(".dll"):
            target = target[:-4]
        elif target.lower().endswith(".so"):
            target = target[:-3]
        elif target.lower().endswith(".dylib"):
            target = target[:-6]
        return target

    def _set_srcdir2(self):
        """Set srcdir2 to compile target. Default is None.

        Parameters
        ----------

        Returns
        -------

        """
        if self.srcdir2 is None:
            if self._get_base_target() in ("libmf6",):
                self.srcdir2 = str(Path(self.download_dir) / "src")
        return

    def _set_sharedobject(self):
        """Set sharedobject to compile target. Default is None.

        Parameters
        ----------

        Returns
        -------

        """
        if self._get_base_target() in ("libmf6",):
            self.sharedobject = True
        else:
            self.sharedobject = False

            # remove any shared compiler options
            for flag in (
                "-fPIC",
                "-shared",
                "-dll",
                "-dynamiclib",
                "-static-intel",
            ):
                if self.fflags is not None:
                    self.fflags = self.fflags.replace(flag, "")
                if self.cflags is not None:
                    self.cflags = self.cflags.replace(flag, "")
                if self.syslibs is not None:
                    self.syslibs = self.syslibs.replace(flag, "")
        return

    def _set_extrafiles(self):
        """Set extrafiles to compile target. Default is None.

        Parameters
        ----------

        Returns
        -------

        """
        extrafiles = self.extrafiles
        if extrafiles is None:
            if self._get_base_target() in ("zbud6",):
                extrafiles = [
                    "../../../src/Utilities/CharString.f90",
                    "../../../src/Utilities/ArrayHandlers.f90",
                    "../../../src/Utilities/ArrayReaders.f90",
                    "../../../src/Utilities/BlockParser.f90",
                    "../../../src/Utilities/Budget.f90",
                    "../../../src/Utilities/Constants.f90",
                    "../../../src/Utilities/compilerversion.F90",
                    "../../../src/Utilities/ErrorUtil.f90",
                    "../../../src/Utilities/FeatureFlags.f90",
                    "../../../src/Utilities/GeomUtil.f90",
                    "../../../src/Utilities/MathUtil.f90",
                    "../../../src/Utilities/InputOutput.f90",
                    "../../../src/Utilities/kind.f90",
                    "../../../src/Utilities/LongLineReader.f90",
                    "../../../src/Utilities/OpenSpec.f90",
                    "../../../src/Utilities/sort.f90",
                    "../../../src/Utilities/defmacro.F90",
                    "../../../src/Utilities/Sim.f90",
                    "../../../src/Utilities/SimVariables.f90",
                    "../../../src/Utilities/version.f90",
                    "../../../src/Utilities/Message.f90",
                    "../../../src/Utilities/GridFileReader.f90",
                    "../../../src/Utilities/HashTable.f90",
                ]

            # evaluate extrafiles type
            if extrafiles:
                srcdir = os.path.abspath(self.srcdir)
                if isinstance(extrafiles, list):
                    for idx, value in enumerate(extrafiles):
                        fpth = str(Path(srcdir) / value)
                        extrafiles[idx] = os.path.normpath(fpth)
                elif isinstance(extrafiles, str):
                    fpth = str(Path(srcdir) / extrafiles)
                    extrafiles = os.path.normpath(fpth)
                else:
                    msg = "invalid extrafiles format - must be a list or string"
                    raise ValueError(msg)

            # reset extrafiles
            self.extrafiles = extrafiles

        return

    def _set_excludefiles(self):
        """Set excludefiles to compile target. Default is None.

        Parameters
        ----------

        Returns
        -------

        """
        if self.excludefiles is None:
            if self._get_base_target() in ("libmf6",):
                self.excludefiles = [str(Path(self.download_dir) / "src" / "mf6.f90")]
        return

    def build(self, target=None, srcdir=None, modify_exe_name=False):
        """Build the target.

        Parameters
        ----------
        target : str
            target name. If target is None self.target is used.
            (default is None)
        srcdir : str
            path to directory with source files. (default is None)
        modify_exe_name : bool
            boolean that determines if the target name can be modified to
            include precision (dbl) and debugging (d) indicators.

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
            self.srcdir = str(Path(self.download_dir) / prog_dict.srcdir)

        # set mesondir for a downloaded target that provides a meson build file
        self._set_mesondir()

        # set include_subdirs for known targets
        self._set_include_subdirs()

        # set srcdir2 for known targets
        self._set_srcdir2()

        # set extrafiles for known targets
        self._set_extrafiles()

        # set excludefiles for known targets
        self._set_excludefiles()

        # set sharedobject for known targets
        self._set_sharedobject()

        self.target = self.update_target(self.target, modify_target=modify_exe_name)

        build_target = self.set_build_target_bool()

        if build_target:
            # print Pymake() settings
            if self.verbose:
                self._print_settings()

            # download url if it has not been downloaded
            if self.download is not None:
                self.download_url()

            # update source code, if necessary. the source update for the
            # MODFLOW 6 targets only removes the files that need an external
            # library, and the meson build file MODFLOW 6 provides lists
            # those files and excludes them from the build itself, so they
            # are only removed when pymake defines the build
            # a makefile is written when only a makefile is asked for, so the
            # source files it lists are the ones a makefile can build
            if self.makefile_only:
                self.makefile = True

            external_only = self._get_base_target() in ("mf6", "libmf6", "zbud6")
            # a makefile is written from the source pymake finds, so the
            # files are removed for a makefile whichever build file is used
            # the files are only kept for a build file the target provides,
            # which has to be there. a generated build file lists the source
            # files pymake finds, so it cannot build them either
            provided_meson = (
                self.mesondir == self.download_dir
                and not self.makefile
                and (Path(self.mesondir) / "meson.build").is_file()
            )

            replace_function = _build_replace(self.target)
            if external_only and provided_meson:
                replace_function = None
            if replace_function is not None:
                if self.verbose:
                    msg = f"replacing select source files for {self.target}\n"
                    print(msg)

                # execute select replace function
                replace_function(
                    self.srcdir,
                    cc=self.cc,
                    double=self.double,
                )

            # write message
            print(f"compiling...{self.target}")

            # build the target
            self.returncode = main(
                srcdir=self.srcdir,
                target=self.target,
                fc=self.fc,
                cc=self.cc,
                makeclean=self.makeclean,
                double=self.double,
                debug=self.debug,
                include_subdirs=self.include_subdirs,
                fflags=self.fflags,
                cflags=self.cflags,
                syslibs=self.syslibs,
                makefile=self.makefile,
                makefile_only=self.makefile_only,
                makefiledir=self.makefiledir,
                srcdir2=self.srcdir2,
                extrafiles=self.extrafiles,
                excludefiles=self.excludefiles,
                sharedobject=self.sharedobject,
                appdir=self.appdir,
                verbose=self.verbose,
                inplace=self.inplace,
                mesondir=self.mesondir,
            )

        # issue error if target was not built
        if self.returncode != 0:
            raise FileNotFoundError(f"could not build {self.target}")
        # add target to list of targets
        else:
            self.update_build_targets()

        return self.returncode

    def update_build_targets(self):
        """Add target to build_targets list if it is not in the list.

        Returns
        -------

        """
        if os.path.abspath(self.target) not in self.build_targets:
            if self.verbose:
                print(f"adding {self.target} to build_targets list")
            self.build_targets.append(os.path.abspath(self.target))

        return

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
        # add extension to target on windows or if shared object
        if sys.platform.lower() == "win32":
            if self.sharedobject:
                ext = ".dll"
            else:
                ext = ".exe"
        elif sys.platform.lower() == "darwin":
            if self.sharedobject:
                ext = ".dylib"
            else:
                ext = None
        else:
            if self.sharedobject:
                ext = ".so"
            else:
                ext = None

        if ext is not None:
            if Path(target).suffix.lower() != ext:
                target += ext

        # add double and debug to target name
        if modify_target:
            if self.double:
                pth = Path(target)
                filename, file_extension = str(pth.with_suffix("")), pth.suffix
                if "dbl" not in filename.lower():
                    target = filename + "dbl" + file_extension
            if self.debug:
                pth = Path(target)
                filename, file_extension = str(pth.with_suffix("")), pth.suffix
                if filename.lower()[-1] != "d":
                    target = filename + "d" + file_extension
        return target
