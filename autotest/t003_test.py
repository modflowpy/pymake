from __future__ import print_function
import os
import shutil
import pymake
import flopy

# define program data
target = 'mfusg'
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join('temp')
if not os.path.exists(dstpth):
    os.makedirs(dstpth)

mfusgpth = os.path.join(dstpth, prog_dict.dirname)
expth = os.path.join(mfusgpth, 'test')

srcpth = os.path.join(mfusgpth, prog_dict.srcdir)
epth = os.path.abspath(os.path.join(dstpth, target))


def edit_namefiles():
    namefiles = pymake.get_namefiles(expth)
    for namefile in namefiles:
        # read existing namefile
        f = open(namefile, 'r')
        lines = f.read().splitlines()
        f.close()
        # convert file extensions to lower case
        f = open(namefile, 'w')
        for line in lines:
            t = line.split()
            fn, ext = os.path.splitext(t[2])
            f.write('{:15s} {:3s} {} '.format(t[0], t[1],
                                              '{}{}'.format(fn, ext.lower())))
            if len(t) > 3:
                f.write('{}'.format(t[3]))
            f.write('\n')
        f.close()


def get_namefiles():
    exclude_tests = ('7_swtv4_ex',)
    namefiles = pymake.get_namefiles(expth, exclude=exclude_tests)
    simname = pymake.get_sim_name(namefiles, rootpth=expth)
    return zip(namefiles, simname)


def compile_code():
    # Remove the existing mfusg directory if it exists
    if os.path.isdir(mfusgpth):
        shutil.rmtree(mfusgpth)

    # compile MODFLOW-USG
    pymake.build_program(target=target,
                         download_dir=dstpth,
                         exe_dir=dstpth)


def clean_up():
    # clean up download directory
    print('Removing folder ' + mfusgpth)
    shutil.rmtree(mfusgpth)

    # clean up executable
    print('Removing ' + target)
    os.remove(epth)
    return


def run_mfusg(namepth, dst):
    print('running...{}'.format(dst))
    # setup
    testpth = os.path.join(dstpth, dst)
    pymake.setup(namepth, testpth)

    # run test models
    print('running model...{}'.format(os.path.basename(namepth)))
    success, buff = flopy.run_model(epth, os.path.basename(namepth),
                                    model_ws=testpth, silent=True)
    if success:
        pymake.teardown(testpth)
    assert success is True

    return


def test_compile():
    # compile MODFLOW-USG
    compile_code()


def test_mfusg():
    # edit namefiles
    edit_namefiles()
    # get name files and simulation name
    sim_list = get_namefiles()
    # run models
    for namepth, dst in sim_list:
        yield run_mfusg, namepth, dst


def test_clean_up():
    yield clean_up


if __name__ == "__main__":
    # compile MODFLOW-USG
    compile_code()

    # edit namefiles
    edit_namefiles()

    # get name files and simulation name
    sim_list = get_namefiles()

    # run models
    for namepth, dst in sim_list:
        run_mfusg(namepth, dst)

    # clean up
    clean_up()
