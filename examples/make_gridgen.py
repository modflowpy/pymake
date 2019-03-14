import os
import shutil
import pymake
import flopy


def test_build_gridgen():

    # get current directory
    dstpth = os.path.join('temp')
    if os.path.exists(dstpth):
        shutil.rmtree(dstpth)
    os.makedirs(dstpth)
    os.chdir(dstpth)

    target = 'gridgen'
    dirname = 'gridgen.1.0.02'
    srcdir = os.path.join(dirname, 'src')
    url = "https://water.usgs.gov/ogw/gridgen/{}.zip".format(dirname)
    pymake.download_and_unzip(url)

    pymake.main(srcdir, target, None, 'g++', makeclean=True,
                expedite=False, dryrun=False, double=False, debug=False,
                include_subdirs=True)

    assert os.path.isfile(target), 'Target does not exist.'


    return


if __name__ == "__main__":
    test_build_gridgen()
