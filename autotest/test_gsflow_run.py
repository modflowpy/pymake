import flopy
import pytest
from flaky import flaky

import pymake

RERUNS = 3


# define program data
target = "gsflow"

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# example path
examples = (
    ("sagehen", "prms.control", "Normal completion"),
    ("sagehen", "gsflow.control", "Normal termination of simulation"),
    ("sagehen", "modflow.control", "Normal termination of simulation"),
)

pm = pymake.Pymake(verbose=True)
pm.target = target
pm.makeclean = True


def modify_examples(data_path):
    tags = {
        "..\\input\\prms\\": "../input/prms/",
        ".\\input\\modflow\\": "./input/modflow/",
        "..\\output\\prms\\": "../output/prms/",
        "..\\output\\modflow\\": "../output/modflow/",
        "..\\output\\": "../output/",
    }

    for example, control_file, _ in examples[1:]:
        fpth = data_path / f"{example}/windows/{control_file}"
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

    # modify available control and name files
    base_paths = []
    for example, _, _ in examples:
        temp_path = data_path / f"{example}/windows"
        if temp_path not in base_paths:
            base_paths.append(temp_path)
        temp_path = data_path / f"{example}/input/modflow"
        if temp_path not in base_paths:
            base_paths.append(temp_path)
    file_paths = []
    for base_path in base_paths:
        file_paths += base_path.glob("*.control")
        file_paths += base_path.glob("*.nam")
    for file_path in file_paths:
        with open(file_path) as f:
            lines = f.readlines()
        with open(file_path, "w") as f:
            for line in lines:
                for key, value in tags.items():
                    if key in line:
                        line = line.replace(key, value)
                f.write(line)

    return True


def run_gsflow(exe, path, example, control_file, normal_message):
    model_ws = path / f"{example}/windows"

    # run the flow model
    success, buff = flopy.run_model(
        exe,
        control_file,
        model_ws=model_ws,
        silent=False,
        normal_msg=normal_message,
    )
    if not success:
        print(f"could not run {control_file}")
    return success


@pytest.mark.skip
@flaky(max_runs=RERUNS)
def test_gsflow_build_run(function_tmpdir):
    pm.download_target(target, download_path=function_tmpdir)
    assert pm.download, f"could not download {target} distribution"
    example_path = function_tmpdir / f"{prog_dict.dirname}/data"
    assert modify_examples(example_path)
    for example, control_file, msg in examples:
        assert run_gsflow(
            function_tmpdir / f"{target}",
            example_path,
            example,
            control_file,
            msg,
        ), f"could not run {example}-{control_file}"
