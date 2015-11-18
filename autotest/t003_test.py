from __future__ import print_function
import os
import shutil
import pymake

# set up paths
dstpth = os.path.join('temp')
if not os.path.exists(dstpth):
    os.makedirs(dstpth)
mfusgpth = os.path.join(dstpth, 'mfusg.1_2')
expth = os.path.join(mfusgpth, 'test')

exe_name = 'mfusgr'
srcpth = os.path.join(mfusgpth, 'src')
target = os.path.join(dstpth, exe_name)

def get_namefiles():
    namefiles = []
    last = os.path.split(expth)[1]
    exclude_tests = ('7_swtv4_ex',)
    for dir, subdirs, files in os.walk(expth):
        for file in files:
            if file.endswith('.nam'):
                pth = os.path.join(dir, file)
                t = pth.split(os.sep)
                i = t.index(last)
                dst = ''
                if i < len(t):
                    for d in t[i+1:-1]:
                        dst += '{}_'.format(d)
                dst += t[-1].replace('.nam', '')
                for e in exclude_tests:
                    if e.lower() in dst.lower():
                        continue
                namefiles.append((pth, dst))
    return namefiles

def compile_code():
    # Remove the existing mfusg directory if it exists
    if os.path.isdir(mfusgpth):
        shutil.rmtree(mfusgpth)

    # Download the MODFLOW-USG distribution
    url = 'http://water.usgs.gov/ogw/mfusg/mfusg.1_2_00.zip'
    pymake.download_and_unzip(url, pth=dstpth)

    # Remove extraneous source directories
    dlist = ['zonebudusg', 'serial']
    for d in dlist:
        dname = os.path.join(srcpth, d)
        if os.path.isdir(dname):
            print('Removing ', dname)
            shutil.rmtree(os.path.join(srcpth, d))

    # compile MODFLOW-USG
    pymake.main(srcpth, target, 'gfortran', 'gcc', makeclean=True,
                expedite=False, dryrun=False, double=False, debug=False)
    assert os.path.isfile(target), 'Target does not exist.'

def clean_up():
    # clean up
    print('Removing folder ' + mfusgpth)
    shutil.rmtree(mfusgpth)
    print('Removing ' + target)
    os.remove(target)
    return

def run_mfusg(namepth, dst):
    print('running...{}'.format(dst))
    # setup
    testpth = os.path.join(dstpth, dst)
    pymake.setup(namepth, testpth)

    # edit name file
    pth = os.path.join(testpth, os.path.basename(namepth))

    # run test models
    print('running model...{}'.format(os.path.basename(namepth)))
    epth = os.path.join('..', exe_name)
    success, buff = pymake.run_model(epth, os.path.basename(namepth),
                                     model_ws=testpth, silent=True)
    if success:
        pymake.teardown(testpth)
    assert success is True

    return

def test_mfusg():
    # compile MODFLOW-USG
    compile_code()
    # get name files and simulation name
    namefiles = get_namefiles()
    # run models
    for namepth, dst in namefiles:
        yield run_mfusg, namepth, dst

def test_clean_up():
    yield clean_up
    
if __name__ == "__main__":
    # compile MODFLOW-USG
    compile_code()
    # get name files and simulation name
    namefiles = get_namefiles()
    # run models
    for namepth, dst in namefiles:
        run_mfusg(namepth, dst)
    # clean up
    clean_up()
