import os
import sys
import shutil
import json
import pymake
import flopy

import pytest

cpth = os.path.abspath(os.path.join("temp", "t011"))
# make the directory if it does not exist
if not os.path.isdir(cpth):
    os.makedirs(cpth)


def test_usgsprograms():
    print("test_usgsprograms()")
    upd = pymake.usgs_program_data().get_program_dict()

    all_keys = list(upd.keys())

    get_keys = pymake.usgs_program_data.get_keys()

    msg = "the keys from program_dict are not equal to .get_keys()"
    assert all_keys == get_keys, msg

    return


def test_target_key_error():
    print("test_target_key_error()")
    with pytest.raises(KeyError):
        pymake.usgs_program_data.get_target("error")


def test_target_keys():
    print("test_target_keys()")
    prog_dict = pymake.usgs_program_data().get_program_dict()
    targets = pymake.usgs_program_data.get_keys()
    for target in targets:
        target_dict = pymake.usgs_program_data.get_target(target)
        test_dict = prog_dict[target]

        msg = (
            "dictionary from {} ".format(target)
            + "does not match dictionary from .get_target()"
        )
        assert target_dict == test_dict, msg

    return


def test_usgsprograms_export_json():
    print("test_usgsprograms_export_json()")
    fpth = os.path.join(cpth, "code.test.json")
    pymake.usgs_program_data.export_json(fpth=fpth, current=True)

    # check that the json file was made
    msg = "did not make...{}".format(fpth)
    assert os.path.isfile(fpth), msg

    # test the json export
    with open(fpth, "r") as f:
        json_dict = json.load(f)
    json_keys = list(json_dict.keys())

    current_keys = pymake.usgs_program_data.get_keys(current=True)

    msg = "the number of current keys is not equal to json keys"
    assert len(json_keys) == len(current_keys), msg

    prog_dict = pymake.usgs_program_data().get_program_dict()
    for key, value in json_dict.items():
        temp_dict = prog_dict[key]
        msg = (
            "json dictionary for {} key ".format(key)
            + "is not equal to the .usgs_prog_data dictionary"
        )
        assert value == temp_dict, msg

    return


def test_usgsprograms_load_json_error():
    print("test_usgsprograms_load_json_error()")
    fpth = os.path.join(cpth, "code.test.error.json")
    my_dict = {"mf2005": {"bad": 12, "key": True}}
    pymake.usgs_program_data.export_json(
        fpth=fpth, prog_data=my_dict, update=False
    )

    with pytest.raises(KeyError):
        pymake.usgs_program_data.load_json(fpth=fpth)


def test_usgsprograms_load_json():
    print("test_usgsprograms_load_json()")
    fpth = os.path.join(cpth, "code.test.json")
    json_dict = pymake.usgs_program_data.load_json(fpth)

    msg = "could not load {}".format(fpth)
    assert json_dict is not None, msg

    return


def test_usgsprograms_list_json_error():
    print("test_usgsprograms_list_json_error()")
    fpth = os.path.join(cpth, "does.not.exist.json")
    with pytest.raises(IOError):
        pymake.usgs_program_data.list_json(fpth=fpth)


def test_usgsprograms_list_json():
    print("test_usgsprograms_list_json()")
    fpth = os.path.join(cpth, "code.test.json")
    pymake.usgs_program_data.list_json(fpth=fpth)


def test_shared():
    print("test_shared()")
    target_dict = pymake.usgs_program_data.get_target("libmf6")
    assert target_dict.shared_object, "libmf6 is a shared object"


def test_not_shared():
    print("test_not_shared()")
    target_dict = pymake.usgs_program_data.get_target("mf6")
    assert not target_dict.shared_object, "mf6 is not a shared object"


def test_gnu_make():
    target = "triangle"

    # add test arguments from command line list
    cargs = ("--makefile", "-mc")
    for arg in cargs:
        sys.argv.append(arg)

    # get current directory and change to working directory
    cwd = os.getcwd()
    os.chdir(cpth)

    # build triangle and makefile
    assert pymake.build_apps(target) == 0, "could not build {}".format(target)

    # remove test arguments from command line list
    for arg in cargs:
        sys.argv.remove(arg)

    if sys.platform.lower() == "win32":
        target += ".exe"
    #
    # # return to starting directory
    # os.chdir(cwd)

    # download the source files again
    pm = pymake.Pymake(verbose=True)
    dpth = os.path.join("temp", "triangle1.6", "src")
    pm.download_target(target, download_path=dpth)

    for file in os.listdir(dpth):
        if "triangle" not in file:
            os.remove(os.path.join(dpth, file))
    #
    # # change to working directory
    # os.chdir(cpth)

    # if os.path.isfile("makefile"):
    if os.path.isfile(os.path.join(cpth, "makefile")):
        # clean prior to make
        print("clean {} with makefile".format(target))
        success, buff = flopy.run_model(
            "make",
            None,
            cargs="clean",
            model_ws=cpth,
            report=True,
            normal_msg="rm -rf ./triangle",
            silent=False,
        )
        # retcode = os.system("make clean")

        # build triangle with makefile
        # if retcode == 0:
        if success:
            print("build {} with makefile".format(target))
            success, buff = flopy.run_model(
                "make",
                None,
                model_ws=cpth,
                report=True,
                normal_msg="cc -O2 -o triangle ./obj_temp/triangle.o",
                silent=False,
            )
            # os.system("make")

    # return to starting directory
    os.chdir(cwd)

    assert os.path.isfile(
        os.path.join(cpth, target)
    ), "could not build {} with makefile".format(target)

    return


def test_clean_up():
    shutil.rmtree(cpth)


if __name__ == "__main__":
    # test_usgsprograms()
    # test_target_key_error()
    # test_target_keys()
    # test_usgsprograms_export_json()
    # test_usgsprograms_load_json_error()
    # test_usgsprograms_load_json()
    # test_usgsprograms_list_json_error()
    # test_usgsprograms_list_json()
    # test_shared()
    # test_not_shared()
    test_gnu_make()
    # test_clean_up()
