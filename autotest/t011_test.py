import os
import shutil
import json
import pymake

import pytest

cpth = os.path.abspath(os.path.join("temp", "t011"))
if os.path.isdir(cpth):
    shutil.rmtree(cpth)
os.makedirs(cpth)


def test_usgsprograms():
    print("test_usgsprograms()")
    upd = pymake.usgs_program_data().get_program_dict()

    all_keys = list(upd.keys())

    get_keys = pymake.usgs_program_data.get_keys()

    msg = "the keys from program_dict are not equal to .get_keys()"
    assert all_keys == get_keys, msg


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


def test_clean_up():
    shutil.rmtree(cpth)


if __name__ == "__main__":
    test_usgsprograms()
    test_target_key_error()
    test_target_keys()
    test_usgsprograms_export_json()
    test_usgsprograms_load_json_error()
    test_usgsprograms_load_json()
    test_usgsprograms_list_json_error()
    test_usgsprograms_list_json()
    test_shared()
    test_not_shared()
    # test_clean_up()
