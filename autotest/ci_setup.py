import os
import pathlib as pl
import shutil

import pymake

temp_pth = pl.Path("temp")
if not temp_pth.exists():
    temp_pth.mkdir()
mf6_exdir = temp_pth / "mf6examples"
if mf6_exdir.is_dir():
    shutil.rmtree(mf6_exdir)
gsflow_exdir = temp_pth / "gsflowexamples"
if gsflow_exdir.is_dir():
    shutil.rmtree(gsflow_exdir)


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
    src_folders = []

    for dirName, subdirList, fileList in os.walk(mf6_exdir):
        useModel = True
        for exclude in exclude_models:
            if exclude in dirName:
                useModel = False
                break
        if useModel:
            for exclude in exclude_examples:
                if exclude in dirName:
                    useModel = False
                    break
        if useModel:
            for file_name in fileList:
                if file_name.lower() == "mfsim.nam":
                    if verbose:
                        print(f"Found directory: {dirName}")
                    src_folders.append(dirName)
    src_folders = sorted(src_folders)

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


def download_gsflow_examples(verbose=False):
    """Download gsflow examples and return location of folder"""

    examples_dirs = (
        "sagehen",
        "acfb_dyn_params",
        "acfb_water_use",
    )

    target = "gsflow"
    pm = pymake.Pymake(verbose=True)
    pm.target = target

    # download the gsflow release
    pm.download_target(target, download_path=temp_pth)
    assert pm.download, f"could not download {target} distribution"

    # get program dictionary
    prog_dict = pymake.usgs_program_data.get_target(target)

    # set path to example
    temp_download_dir = temp_pth / prog_dict.dirname
    temp_dir = temp_download_dir / "data"

    print(f"copying files to...{gsflow_exdir}")
    shutil.copytree(temp_dir, gsflow_exdir)

    # create list of examples to test and edit files if necessary
    src_folders = []
    for ex_dir in examples_dirs:
        out_path = gsflow_exdir / ex_dir

        if "sagehen" in ex_dir:
            out_path = out_path / "linux"
            modify_gsflow_sagehen(out_path)
        elif "acfb" in ex_dir:
            shutil.copy(
                out_path / "control/control", out_path / "gsflow.control"
            )

        # add final example path to src_folders list
        src_folders.append(out_path)

    print(f"removing...{temp_download_dir} directory")
    shutil.rmtree(temp_download_dir)

    # create a  list of gsflow examples
    fpth = gsflow_exdir / "gsflowexamples.txt"
    f = open(fpth, "w")
    for idx, folder in enumerate(src_folders):
        if verbose:
            if idx == 0:
                print(f"\n\nGSFLOW examples:\n{78 * '-'}")
            print(f"{idx + 1:>3d}: {folder}")
        f.write(f"{os.path.abspath(folder)}\n")
    f.close()

    return gsflow_exdir.resolve()


def modify_gsflow_sagehen(temp_pth):
    fpth = temp_pth / "gsflow.control"
    with open(fpth) as f:
        lines = f.readlines()
    with open(fpth, "w") as f:
        idx = 0
        while idx < len(lines):
            line = lines[idx]
            if "end_time" in line:
                line += "6\n1\n1981\n"
                idx += 3
            f.write(line)
            idx += 1
    return


if __name__ == "__main__":
    # mf6pth = download_mf6_examples(verbose=True)
    # examples_list(verbose=True)
    gsflowpth = download_gsflow_examples(verbose=True)
