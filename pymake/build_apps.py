import os
import sys
from datetime import datetime

from .usgsprograms import usgs_program_data
from .pymake import Pymake


def build_apps(
    targets=None,
    pymake_object=None,
    download_dir=None,
    appdir=None,
    verbose=None,
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

    Returns
    -------
    returncode : int

    """

    start_time = datetime.now()
    if targets is None:
        targets = usgs_program_data.get_keys(current=True)
    else:
        if isinstance(targets, str):
            targets = [targets]

    code_dict = {}

    if pymake_object is None:
        pmobj = Pymake()
    else:
        if isinstance(pymake_object, Pymake()):
            pmobj = pymake_object
        else:
            msg = "pymake_object ({}) is not of type {}".format(
                type(pymake_object), type(Pymake())
            )
            raise TypeError(msg)

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
                    "{} will be built ".format(target)
                    + 'for the "{}" operating system\n'.format(sys.platform)
                )

        # save initial compiler settings
        if idt == 0:
            fc0 = pmobj.fc
            cc0 = pmobj.cc

        # reset compilers
        if target in ("gridgen",):
            pmobj.fc = "none"
            if pmobj.cc in ("gcc",):
                pmobj.cc = "g++"
            elif pmobj.cc in ("clang",):
                pmobj.cc = "clang++"
        elif target in ("triangle",):
            pmobj.fc = "none"
        elif target in ("mf6",):
            pmobj.cc = "none"
        else:
            pmobj.fc = fc0
            pmobj.cc = cc0

        # reset extrafiles for instances with more than one target
        if idt > 0:
            pmobj.extrafiles = None

        # set double precision flag and whether the executable name
        # can be modified
        if target in ["swtv4"]:
            update_target_name = False
        else:
            update_target_name = True

        # set download information
        download_now = True
        download_clean = True
        download_dir = "temp"

        # modify download if mf6 and also building zonbud6
        if target == "mf6":
            if idt + 1 < len(targets):
                if targets[idt + 1] == "zbud6":
                    download_clean = False
        elif target == "zbud6":
            if idt > 0:
                if targets[idt - 1] == "mf6":
                    download_now = False

        # modify download if mfusg and also building zonbudusg
        if target == "mfusg":
            if idt + 1 < len(targets):
                if targets[idt + 1] == "zonbudusg":
                    download_clean = False
        elif target == "zonbudusg":
            if idt > 0:
                if targets[idt - 1] == "mfusg":
                    download_now = False

        if target in ["mt3dms", "triangle", "mf6beta"]:
            download_verify = False
            timeout = 10
        else:
            download_verify = True
            timeout = 30

        # set target and srcdir
        pmobj.target = target
        pmobj.srcdir = os.path.join(
            download_dir, code_dict[target].dirname, code_dict[target].srcdir
        )

        # determine if single, double, or both should be built
        precision = usgs_program_data.get_precision(target)

        for idx, double in enumerate(precision):
            # set double flag
            pmobj.double = double

            # determine if the target should be built
            build_target = pmobj.set_build_target_bool(
                target=pmobj.update_target(
                    target, modify_target=update_target_name
                )
            )

            # set download boolean
            if idx == 0:
                download = download_now
            else:
                download = False

            # set clean boolean
            if len(precision) > 1:
                if idx < len(precision) - 1:
                    clean = False
                else:
                    clean = download_clean
            else:
                clean = download_clean

            # setup download for target
            if download:
                pmobj.download_setup(
                    target,
                    download_path=download_dir,
                    verify=download_verify,
                    timeout=timeout,
                )

            # build the code
            if build_target:
                pmobj.build(modify_exe_name=update_target_name)

            # clean up the download
            if clean:
                pmobj.download_cleanup()

        # calculate download and compile time
        end_downcomp = datetime.now()
        elapsed = end_downcomp - start_downcomp
        if pmobj.verbose:
            print(
                "elapsed download and compile time (hh:mm:ss.ms): "
                + "{}\n".format(elapsed)
            )

    end_time = datetime.now()
    elapsed = end_time - start_time
    if pmobj.verbose:
        print("elapsed time (hh:mm:ss.ms): {}\n".format(elapsed))

    # compress targets
    if pmobj.returncode == 0:
        pmobj.compress_targets()

    return pmobj.returncode
