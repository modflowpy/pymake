from __future__ import print_function
import os
import shutil
import pymake


def test_seawat():

    # get current directory
    pth = os.getcwd()
    # working directory
    dstpth = os.path.join('temp')
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)
    # change to temp subdirectory
    os.chdir(dstpth)

    # Remove the existing swt_v4_00_05 directory if it exists
    dirname = os.path.join('swt_v4_00_05')
    if os.path.isdir(dirname):
        shutil.rmtree(dirname)

    # Download the SEAWAT distribution
    url = 'http://water.usgs.gov/ogw/seawat/swt_v4_00_05.zip'
    pymake.download_and_unzip(url)

    srcdir = os.path.join(dirname, 'source')
    target = 'swtv4pymake'

    # Remove the parallel and serial folders from the source directory
    dlist = ['parallel', 'serial']
    for d in dlist:
        dname = os.path.join(srcdir, d)
        if os.path.isdir(dname):
            print('Removing ', dname)
            shutil.rmtree(os.path.join(srcdir, d))

    # Replace filespec with standard fortran
    l = "      CHARACTER*20 ACCESS,FORM,ACTION(2)\n" +\
        "      DATA ACCESS/'STREAM'/\n" +\
        "      DATA FORM/'UNFORMATTED'/\n" +\
        "      DATA (ACTION(I),I=1,2)/'READ','READWRITE'/\n"

    fn = os.path.join(srcdir, 'filespec.inc')
    f = open(fn, 'w')
    f.write(l)
    f.close()

    # rename all source files to lower case so compilation doesn't
    # bomb on case-sensitive systems
    srcfiles = os.listdir(srcdir)
    for filename in srcfiles:
        src = os.path.join(srcdir, filename)
        dst = os.path.join(srcdir, filename.lower())
        os.rename(src, dst)

    # compile seawat
    pymake.main(srcdir, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=True, debug=False,
                include_subdirs=False)

    assert os.path.isfile(target) is True

    # create the directory for the output if it doesn't exist
    dstpth = os.path.join(dirname, 'dep')
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)

    # make dependency figures
    pymake.visualize.make_plots(srcdir, dstpth)

    # test that the dependency figure for the MODFLOW-2005 main exists
    testpth = os.path.join(dstpth, 'swt_v4.f.png')
    assert os.path.isfile(testpth) is True


    # # run test models
    # model_ws = [os.path.join(dirname, 'examples', '3_elder'),
    #             os.path.join(dirname, 'examples', '4_hydrocoin'),
    #             os.path.join(dirname, 'examples', '5_saltlake')]
    # exe_name = os.path.join(os.getcwd(), target)
    # namefiles = []
    # exclude = []
    # for ws in model_ws:
    #     for file in os.listdir(ws):
    #         if file.endswith('.nam'):
    #             namefiles.append(file)
    #     for namefile in namefiles:
    #         if namefile in exclude:
    #             continue
    #         print('running model...{}'.format(namefile))
    #         success, buff = pymake.run_model(exe_name, namefile, model_ws=ws, silent=True)
    #         assert success is True

    # change back to the starting directory
    os.chdir(pth)


if __name__ == '__main__':
    test_seawat()
