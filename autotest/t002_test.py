from __future__ import print_function
import os
import shutil
import pymake
import flopy

# set up paths
dstpth = os.path.join('temp')
if not os.path.exists(dstpth):
    os.makedirs(dstpth)
swtpth = os.path.join(dstpth, 'swt_v4_00_05')
expth = os.path.join(swtpth, 'examples')
deppth = os.path.join(swtpth, 'dependencies')

exe_name = 'swtv4r'
srcpth = os.path.join(swtpth, 'source')
target = os.path.join(dstpth, exe_name)

def edit_namefile(namefile):
    # read existing namefile
    f = open(namefile, 'r')
    lines = f.read().splitlines()
    f.close()
    # remove global line
    f = open(namefile, 'w')
    for line in lines:
        if 'global' in line.lower():
            continue
        f.write('{}\n'.format(line))
    f.close()

def get_namefiles():
    exclude_tests = ('7_swtv4_ex', '6_rotation')
    namefiles = pymake.get_namefiles(expth, exclude=exclude_tests)
    simname = pymake.get_sim_name(namefiles, rootpth=expth)
    return zip(namefiles, simname)

def compile_code():
    # Remove the existing swt_v4_00_05 directory if it exists
    if os.path.isdir(swtpth):
        shutil.rmtree(swtpth)

    # Download the SEAWAT distribution
    url = 'http://water.usgs.gov/ogw/seawat/swt_v4_00_05.zip'
    pymake.download_and_unzip(url, pth=dstpth)

    # Remove the parallel and serial folders from the source directory
    dlist = ['parallel', 'serial']
    for d in dlist:
        dname = os.path.join(srcpth, d)
        if os.path.isdir(dname):
            print('Removing ', dname)
            shutil.rmtree(os.path.join(srcpth, d))

    # Replace filespec with standard fortran
    l = "      CHARACTER*20 ACCESS,FORM,ACTION(2)\n" +\
        "      DATA ACCESS/'STREAM'/\n" +\
        "      DATA FORM/'UNFORMATTED'/\n" +\
        "      DATA (ACTION(I),I=1,2)/'READ','READWRITE'/\n"

    fn = os.path.join(srcpth, 'filespec.inc')
    f = open(fn, 'w')
    f.write(l)
    f.close()

    # rename all source files to lower case so compilation doesn't
    # bomb on case-sensitive systems
    srcfiles = os.listdir(srcpth)
    for filename in srcfiles:
        src = os.path.join(srcpth, filename)
        dst = os.path.join(srcpth, filename.lower())
        os.rename(src, dst)

    # compile seawat
    pymake.main(srcpth, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=True, debug=False,
                include_subdirs=False)

    assert os.path.isfile(target) is True, 'Target does not exist.'
    return

def clean_up():
    # clean up
    print('Removing folder ' + swtpth)
    shutil.rmtree(swtpth)
    print('Removing ' + target)
    os.remove(target)
    return

def run_seawat(namepth, dst):
    print('running...{}'.format(dst))
    # setup
    testpth = os.path.join(dstpth, dst)
    pymake.setup(namepth, testpth)

    # edit name file
    pth = os.path.join(testpth, os.path.basename(namepth))
    edit_namefile(pth)

    # run test models
    print('running model...{}'.format(os.path.basename(namepth)))
    epth = os.path.abspath(target)
    success, buff = flopy.run_model(epth, os.path.basename(namepth),
                                    model_ws=testpth, silent=True)
    if success:
        pymake.teardown(testpth)
    assert success is True

    return

def build_seawat_dependency_graphs():
    # build dependencies output directory
    if not os.path.exists(deppth):
        os.makedirs(deppth)
    # build dependency graphs
    print('building dependency graphs')
    pymake.visualize.make_plots(srcpth, deppth)
    # test that the dependency figure for the SEAWAT main exists
    findf = os.path.join(deppth, 'swt_v4.f.png')
    assert os.path.isfile(findf) is True
    return

def test_compile():
    # compile seawat
    yield compile_code

def test_seawat():
    # get name files and simulation name
    namefiles = get_namefiles()
    # run models
    for namepth, dst in namefiles:
        yield run_seawat, namepth, dst

def test_dependency_graphs():
    # build dependency graphs
    yield build_seawat_dependency_graphs

def test_clean_up():
    yield clean_up

if __name__ == '__main__':
    # compile seawat
    compile_code()
    # get name files and simulation name
    namefiles = get_namefiles()
    # run models
    for namepth, dst in namefiles:
        run_seawat(namepth, dst)
    # build dependency graphs
    build_seawat_dependency_graphs()
    # clean up
    clean_up()
