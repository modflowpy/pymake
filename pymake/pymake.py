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
import time
import shutil

from .build_program import set_compiler, set_extrafiles, set_include_subdirs
from .compiler_switches import get_osname
from .download import download_and_unzip
from .pymake_base import main
from .usgsprograms import usgs_program_data


class Pymake:
    """
    Pymake class for interacting with pymake functionality. This is essentially
    a wrapper for all of the pymake functions needed to download and build
    a target.

    """

    def __init__(self, name="pymake"):
        self.name = name
        self.url = None
        self.download_path = None
        self.download_dir = None
        self.srcdir = None
        self.returncode = 0
        self.build_targets = []

    def clean_targets(self):
        """

        Returns
        -------

        """
        for target in self.build_targets:
            if os.path.exists(target):
                msg = "removing '{}'".format(target)
                os.remove(target)
            else:
                msg = "'{}' does not exist".format(target)
            print(msg)
        return

    def download_target(
        self, target, url=None, download_path=".", verify=True, timeout=30
    ):
        """

        Parameters
        ----------
        target
        url
        download_path
        verify
        timeout

        Returns
        -------

        """
        prog_dict = usgs_program_data.get_target(target)

        # set url
        if url is None:
            url = prog_dict.url
        self.url = url

        # set download_dir
        self.download_path = download_path
        self.download_dir = os.path.join(download_path, prog_dict.dirname)

        return download_and_unzip(
            self.url, pth=self.download_path, verify=verify, timeout=timeout
        )

    def download_cleanup(self):
        """

        Returns
        -------

        """
        if os.path.exists(self.download_dir):
            ntries = 10
            for itries in range(ntries):
                # wait to delete on windows
                if get_osname() == "win32":
                    time.sleep(3)

                # remove the directory
                try:
                    shutil.rmtree(self.download_dir)
                    print(
                        "removing download directory...'{}'".format(
                            self.download_dir
                        )
                    )
                    break
                except:
                    msg = "    removal attempt {:>2d} ".format(itries + 1)
                    msg += "of {:>2d}".format(ntries)
                    print(msg)

            # wait prior to returning on windows
            if get_osname() == "win32":
                time.sleep(6)

        return

    def build(
        self,
        target="mf6",
        srcdir=None,
        fc=None,
        cc=None,
        makeclean=True,
        expedite=False,
        dryrun=False,
        double=False,
        debug=False,
        include_subdirs=None,
        fflags=None,
        cflags=None,
        syslibs=None,
        arch="intel64",
        makefile=False,
        srcdir2=None,
        extrafiles=None,
        excludefiles=None,
        sharedobject=False,
        appdir=None,
    ):
        """

        Parameters
        ----------
        targets

        Returns
        -------

        """
        prog_dict = usgs_program_data.get_target(target)
        if srcdir is None:
            srcdir = os.path.join(self.download_dir, prog_dict.srcdir)
        self.srcdir = srcdir

        if fc is None or cc is None:
            tfc, tcc = set_compiler(target)
            if fc is None:
                fc = tfc
            if cc is None:
                cc = tcc

        if extrafiles is None:
            extrafiles = set_extrafiles(target, self.download_path)

        if include_subdirs is None:
            include_subdirs = set_include_subdirs(target)

        # process target
        if appdir is not None:
            target = os.path.join(appdir, os.path.basename(target))
        else:
            target = os.path.join(".", os.path.basename(target))

        # add target to list of targets
        if os.path.abspath(target) not in self.build_targets:
            self.build_targets.append(os.path.abspath(target))

        self.returncode = main(
            srcdir=self.srcdir,
            target=target,
            fc=fc,
            cc=cc,
            makeclean=makeclean,
            expedite=expedite,
            dryrun=dryrun,
            double=double,
            debug=debug,
            include_subdirs=include_subdirs,
            fflags=fflags,
            cflags=cflags,
            syslibs=syslibs,
            arch=arch,
            makefile=makefile,
            srcdir2=srcdir2,
            extrafiles=extrafiles,
            excludefiles=excludefiles,
            sharedobject=sharedobject,
        )

        if self.returncode != 0:
            raise FileNotFoundError("could not build {}".format(target))
        return self.returncode
