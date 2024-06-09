import os
import pathlib as pl
import shutil

from modflow_devtools.misc import get_model_paths

import pymake

temp_pth = pl.Path("temp")
if not temp_pth.exists():
    temp_pth.mkdir()
mf6_exdir = temp_pth / "mf6examples"
if mf6_exdir.is_dir():
    shutil.rmtree(mf6_exdir)


def download_mf6_examples(verbose=False):
    """Download mf6 examples and return location of folder"""

    target = "mf6"
    pm = pymake.Pymake(verbose=True)
    pm.target = target

    # download the modflow 6 release
    pm.download_target(target, download_path=temp_pth)
    assert pm.download, f"could not download {target} distribution"

    # get program dictionary
    prog_dict = pymake.usgs_program_data.get_target(target)

    # set path to example
    temp_download_dir = os.path.join(temp_pth, prog_dict.dirname)
    temp_dir = os.path.join(temp_download_dir, "examples")

    print(f"copying files to...{mf6_exdir}")
    shutil.copytree(temp_dir, mf6_exdir)

    print(f"removing...{temp_download_dir} directory")
    shutil.rmtree(temp_download_dir)

    return os.path.abspath(mf6_exdir)


def examples_list(verbose=False):
    """Build list of examples

    Returns
    -------

    """
    exclude_models = ("lnf",)
    exclude_examples = (
        "sagehen",
        "ex-gwt-keating",
    )

    src_folders = get_model_paths(mf6_exdir)
    fpth = os.path.join(mf6_exdir, "mf6examples.txt")
    f = open(fpth, "w")
    for idx, folder in enumerate(src_folders):
        if verbose:
            if idx == 0:
                print(f"\n\nMODFLOW 6 examples:\n{78 * '-'}")
            print(f"{idx + 1:>3d}: {folder}")
        f.write(f"{os.path.abspath(folder)}\n")
    f.close()

    return


if __name__ == "__main__":
    mf6pth = download_mf6_examples(verbose=True)
    examples_list(verbose=True)
