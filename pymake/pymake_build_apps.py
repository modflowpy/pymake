"""Function to build MODFLOW-based models and other utility software based on
targets defined in the usgsprograms database (usgsprograms.txt). The
usgsprograms database can be queried using functions in the usgsprograms
module. An example of using :code:`pymake.build_apps()` to build MODFLOW 6 is:

.. code-block:: python

    import pymake
    pymake.build_apps(["mf6",])

which will download the latest MODFLOW 6 software release, compile the code,
and delete the downloaded files after successfully building the application.
Multiple applications can be built by adding additional targets to the tuple
in :code:`pymake.build_apps()`. For example, MODFLOW 6 and MODFLOW-2005 could
be built by specifying:

.. code-block:: python

    import pymake
    pymake.build_apps(["mf6","mf2005"]))

Applications are built in the order they are listed in the list. All valid
USGS applications are built if no list is passed to
:code:`pymake.build_apps()`.

"""

import os
import shutil
import sys
from datetime import datetime

from .pymake import Pymake
from .pymake_base import get_temporary_directories
from .utils.usgsprograms import usgs_program_data


def build_apps(
    targets=None,
    pymake_object=None,
    download_dir=None,
    appdir=None,
    verbose=None,
    release_precision=True,
    meson=False,
    mesondir=".",
    clean=True,
):
    """Build all of the current targets or a subset of targets.

    Parameters
    ----------
    targets : str or list of str
        targets to build. If targets is None, all current targets will
        be build. Default is None
    pymake_object : Pymake()
        Pymake object created outside of build_apps
    download_dir : str
        download directory path
    appdir : str
        target path
    release_precision : bool
        boolean indicating if only the release precision version should be
        build. If release_precision is False, then the release precision
        version will be compiled along with a double precision version of
        the program for programs where the standard_switch and double_switch
        in usgsprograms.txt is True. default is True.
    meson : bool
        boolean indicating that the executable should be built using the
        meson build system. (default is False)
    mesondir : str
        Main meson.build file path
    clean : bool
        boolean determining of final download should be removed

    Returns
    -------
    returncode : int
        integer value indicating successful completion (0) or failure (>0)

    """

    start_time = datetime.now()

    # intercept all string (":") from make-program
    if isinstance(targets, str):
        if targets == ":":
            targets = None

    # set targets
    if targets is None:
        targets = usgs_program_data.get_keys(current=True)
    else:
        if isinstance(targets, str):
            targets = [targets]

    code_dict = {}

    if pymake_object is None:
        pmobj = Pymake()
    else:
        if isinstance(pymake_object, Pymake):
            pmobj = pymake_object
        else:
            msg = (
                f"pymake_object ({type(pymake_object)}) "
                + f"is not of type {type(Pymake())}"
            )
            raise TypeError(msg)

    # set base path for temporary directories
    if appdir is None:
        base_pth = "."
    else:
        base_pth = os.path.dirname(appdir)

    # set meson variable if a pymake object was not passed in
    if pymake_object is None:
        pmobj.meson = meson
        pmobj.mesondir = mesondir
    else:
        if pmobj.meson != meson:
            pmobj.meson = meson
        if pmobj.mesondir != mesondir:
            pmobj.mesondir = mesondir

    # clean any existing temporary directories
    temp_pths = get_temporary_directories(base_pth)
    for pth in temp_pths:
        if os.path.isdir(pth):
            shutil.rmtree(pth)

    # set object to clean after each build
    pmobj.makeclean = True

    # reset variables based on passed args
    if download_dir is not None:
        pmobj.download_dir = download_dir
    if appdir is not None:
        pmobj.appdir = appdir
    if verbose is not None:
        pmobj.verbose = verbose

    for idt, target in enumerate(targets):
        start_downcomp = datetime.now()

        code_dict[target] = usgs_program_data.get_target(target)

        # write system information
        if idt == 0:
            if pmobj.verbose:
                print(
                    f"{target} will be built "
                    + f'for the "{sys.platform}" operating system\n'
                )

        # save initial compiler settings
        if idt == 0:
            fc0 = pmobj.fc
            cc0 = pmobj.cc
            fflags0 = pmobj.fflags
            cflags0 = pmobj.cflags
            syslibs0 = pmobj.syslibs
        # reset fortran, c/c++, and syslib flags
        else:
            pmobj.fflags = fflags0
            pmobj.cflags = cflags0
            pmobj.syslibs = syslibs0

        # reset compilers
        if target in ("gridgen",):
            pmobj.fc = "none"
            if pmobj.cc in ("gcc",):
                pmobj.cc = "g++"
            elif pmobj.cc in ("clang",):
                pmobj.cc = "clang++"
        elif target in ("triangle",):
            pmobj.fc = "none"
        elif target in ("mf6", "libmf6"):
            pmobj.cc = "none"
        else:
            pmobj.fc = fc0
            pmobj.cc = cc0

        # set sharedobject
        if target in ("libmf6",):
            pmobj.sharedobject = True
        else:
            pmobj.sharedobject = False

        # reset srcdir2 - TODO make more robust
        if target not in ("libmf6",):
            pmobj.srcdir2 = None

        # reset extrafiles for instances with more than one target
        if idt > 0:
            pmobj.extrafiles = None

        # set double precision flag and whether the executable name
        # can be modified
        if target in ("swtv4",):
            update_target_name = False
        else:
            update_target_name = True

        # set download information
        if download_dir is None:
            download_dir = "temp"
        download_verify = True
        timeout = 30

        # reset meson
        if target in ("prms",):
            pmobj.meson = True
            pmobj.inplace = True

        # set target and srcdir
        pmobj.target = target.replace("dev", "")
        pmobj.srcdir = os.path.join(
            download_dir, code_dict[target].dirname, code_dict[target].srcdir
        )

        # determine if single, double, or both should be built
        precision = usgs_program_data.get_precision(target)

        # just build the first precision in precision list if
        # standard_precision is True
        if release_precision:
            precision = precision[0:1]

        for double in precision:
            # set double flag
            pmobj.double = double

            # determine if the target should be built
            build_target = pmobj.set_build_target_bool(
                target=pmobj.update_target(
                    target, modify_target=update_target_name
                )
            )

            # setup download for target
            pmobj.download_setup(
                target,
                download_path=download_dir,
                verify=download_verify,
                timeout=timeout,
            )

            # build the code
            if build_target:
                pmobj.build(modify_exe_name=update_target_name)
            # add target to build_targets list, if necessary
            else:
                pmobj.update_build_targets()

        # calculate download and compile time
        end_downcomp = datetime.now()
        elapsed = end_downcomp - start_downcomp
        if pmobj.verbose:
            print(
                "elapsed download and compile time (hh:mm:ss.ms): "
                + f"{elapsed}\n"
            )

    end_time = datetime.now()
    elapsed = end_time - start_time
    if pmobj.verbose:
        print(f"elapsed time (hh:mm:ss.ms): {elapsed}\n")

    # compress targets
    if pmobj.returncode == 0:
        pmobj.compress_targets()

    # execute final Pymake object operations
    if clean:
        pmobj.finalize()

    return pmobj.returncode
