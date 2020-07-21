import os
import sys
import shutil
import pymake
import flopy

# define program data
target = "mt3dusgs"

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join("temp")
if not os.path.exists(dstpth):
    os.makedirs(dstpth)

mtusgsver = prog_dict.version
mtusgspth = os.path.join(dstpth, prog_dict.dirname)
emtusgs = os.path.abspath(os.path.join(dstpth, target))

mfnwt_target = "mfnwt"
temp_dict = pymake.usgs_program_data().get_target(mfnwt_target)
emfnwt = os.path.abspath(os.path.join(dstpth, mfnwt_target))

mf6_target = "mf6"
temp_dict = pymake.usgs_program_data().get_target(mf6_target)
emf6 = os.path.abspath(os.path.join(dstpth, mf6_target))

if sys.platform.lower() == "win32":
    ext = ".exe"
    emtusgs += ext
    emfnwt += ext
    emf6 += ext

# example path
expth = os.path.join(mtusgspth, "data")

# set up pths and exes
epths = [emtusgs, emfnwt, emf6]

pm = pymake.Pymake(verbose=True)
pm.target = target
pm.appdir = dstpth


def get_example_dirs():
    if os.path.exists(emtusgs):
        exclude_dirs = ["Keating", "Keating_UZF"]

        upd = pymake.usgs_program_data()

        # exclude additional directories based on version of codes
        # MODFLOW-NWT
        ver = upd.get_version("mfnwt")
        if ver == "1.2.0":
            exclude_dirs += [
                "UZT_NonLin",
                "UZT_Disp_Lamb01_TVD",
                "UZT_Disp_Lamb1",
                "UZT_Disp_Lamb10",
            ]

        # create list of example directories to test
        exdirs = [
            o
            for o in sorted(os.listdir(expth))
            if os.path.isdir(os.path.join(expth, o)) and o not in exclude_dirs
        ]
    else:
        exdirs = [None]
    return exdirs


def download_src():
    # Remove the existing target download directory if it exists
    if os.path.isdir(mtusgspth):
        shutil.rmtree(mtusgspth)

    # download the target
    pm.download_target(target, download_path=dstpth)


def run_mt3dusgs(temp_dir):
    if os.path.exists(emtusgs):
        model_ws = os.path.join(expth, temp_dir)

        files = [
            f
            for f in os.listdir(model_ws)
            if os.path.isfile(os.path.join(model_ws, f))
        ]

        mf_nam = None
        mt_nam = None
        flow_model = None
        for f in files:
            if "_mf.nam" in f.lower():
                mf_nam = f
                flow_model = "mfnwt"
            if "_mt.nam" in f.lower():
                mt_nam = f
            if f == "mfsim.nam":
                mf_nam = f
                flow_model = "mf6"

        msg = "A MODFLOW name file not present in {}".format(model_ws)
        assert mf_nam is not None, msg

        msg = "A MT3D-USGS name file not present in {}".format(model_ws)
        assert mt_nam is not None, msg

        # run the flow model
        msg = "{}".format(emfnwt)
        if mf_nam is not None:
            msg += " {}".format(os.path.basename(mf_nam))
        if flow_model == "mfnwt":
            nam = mf_nam
            eapp = emfnwt
        elif flow_model == "mf6":
            nam = None
            eapp = emf6
        success, buff = flopy.run_model(
            eapp, nam, model_ws=model_ws, silent=False
        )

        assert success, "could not run...{}".format(msg)

        # run the MT3D-USGS model
        print("running model...{}".format(mt_nam))
        success, buff = flopy.run_model(
            emtusgs,
            mt_nam,
            model_ws=model_ws,
            silent=False,
            normal_msg="Program completed.",
        )
        if not success:
            errmsg = "could not run {}".format(mtnam)
    else:
        success = False
        errmsg = "could not run {}".format(os.path.basename(emtusgs))

    assert success, errmsg

    return


def clean_up():
    print("Removing temporary build directories")
    dirs_temp = [os.path.join("obj_temp"), os.path.join("mod_temp")]
    for d in dirs_temp:
        if os.path.isdir(d):
            shutil.rmtree(d)

    # finalize pymake object
    pm.finalize()

    for epth in epths:
        if os.path.isfile(epth):
            print("Removing '" + epth + "'")
            os.remove(epth)


def test_download_exes():
    pymake.getmfexes(dstpth, exes=("mfnwt", "mf6"), verbose=True)
    return


def test_download():
    download_src()


def test_compile():
    pm.build()


def test_mt3dusgs():
    for dn in get_example_dirs():
        yield run_mt3dusgs, dn


def test_clean_up():
    clean_up()


if __name__ == "__main__":
    test_download_exes()
    test_download()
    test_compile()
    for dn in get_example_dirs():
        run_mt3dusgs(dn)
    test_clean_up()
