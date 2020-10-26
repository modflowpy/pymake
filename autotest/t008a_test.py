import os
import shutil
import pymake

mf6_exdir = os.path.join('temp', "mf6examples")


def download_mf6_examples():
    """
    Download mf6 examples and return location of folder

    """

    # set url
    url = "https://github.com/MODFLOW-USGS/modflow6-examples/releases/" + \
          "download/current/modflow6-examples.zip"

    # create folder for mf6 distribution download
    cpth = os.getcwd()
    print('create...{}'.format(mf6_exdir))
    if os.path.exists(mf6_exdir):
        shutil.rmtree(mf6_exdir)
    os.makedirs(mf6_exdir)
    os.chdir(mf6_exdir)

    # Download the distribution
    pymake.download_and_unzip(url, verify=True)

    # change back to original path
    os.chdir(cpth)

    # return the absolute path to the distribution
    mf6path = os.path.abspath(mf6_exdir)

    return mf6path


def examples_list(verbose=False):
    """Build list of examples

    Returns
    -------

    """
    exclude_models = (
        "lnf",
    )
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
                        print('Found directory: {}'.format(dirName))
                    src_folders.append(dirName)
    src_folders = sorted(src_folders)

    fpth = os.path.join(mf6_exdir, "mf6examples.txt")
    f = open(fpth, "w")
    for folder in src_folders:
        f.write("{}\n".format(os.path.abspath(folder)))
    f.close()

    return


def test_mf6_setup():
    mf6path = download_mf6_examples()


def test_mf6_examples(verbose=True):
    examples_list(verbose=verbose)


if __name__ == "__main__":
    mf6pth = test_mf6_setup()
    examples_list()
