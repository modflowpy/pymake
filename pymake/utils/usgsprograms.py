"""Utility functions to extract information for a target from the USGS
application database. Available functionality includes:

1. Get a list of available targets
2. Get data for a specific target
3. Get a dictionary with the data for all targets
4. Get the current version of a target
5. Get a list indicating if single and double precision versions of the
   target application should be built
6. Functions to load, update, and export a USGS-style "code.json" json file
   containing information in the USGS application database

A table listing the available pymake targets is included below:

.. csv-table:: Available pymake targets
   :file: ./usgsprograms.txt
   :widths: 10, 10, 10, 20, 10, 10, 10, 10, 10
   :header-rows: 1

"""

import datetime
import json
import os
import sys
from pathlib import Path

from .download import _request_header, zip_all


class dotdict(dict):
    """dot.notation access to dictionary attributes."""

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


# data file containing the USGS program data
program_data_file = "usgsprograms.txt"

# keys to create for each target
target_keys = (
    "version",
    "current",
    "url",
    "dirname",
    "srcdir",
    "standard_switch",
    "double_switch",
    "shared_object",
    "url_download_asset_date",
)


def _str_to_bool(s):
    """Convert "True" and "False" strings to a boolean.

    Parameters
    ----------
    s : str
        String representation of boolean

    Returns
    -------

    """
    if s == "True":
        return True
    elif s == "False":
        return False
    else:
        msg = f'Invalid string passed - "{s}"'
        raise ValueError(msg)


class usgs_program_data:
    """USGS program database class."""

    def __init__(self):
        """USGS program database init."""
        self._program_dict = self._build_usgs_database()

    def _build_usgs_database(self):
        """Build the USGS program database.

        Returns
        -------

        """
        # pth = os.path.dirname(os.path.abspath(pymake.__file__))
        pth = os.path.dirname(os.path.abspath(__file__))
        fpth = os.path.join(pth, program_data_file)
        url_in = open(fpth, "r").read().split("\n")

        program_data = {}
        for line in url_in[1:]:
            # skip blank lines
            if len(line.strip()) < 1:
                continue
            # parse comma separated line
            t = [item.strip() for item in line.split(sep=",")]
            # programmatically build a dictionary for each target
            d = {}
            for idx, key in enumerate(target_keys):
                if key in ("url_download_asset_date",):
                    value = None
                else:
                    value = t[idx + 1]
                if key in (
                    "current",
                    "standard_switch",
                    "double_switch",
                    "shared_object",
                ):
                    value = _str_to_bool(value)
                d[key] = value

            # make it possible to access each key with a dot (.)
            d = dotdict(d)
            program_data[t[0]] = d

        return dotdict(program_data)

    def _target_data(self, key):
        """Get the dictionary for the target key.

        Parameters
        ----------
        key : str
            Program key (name)

        Returns
        -------
        return : dict
            dictionary with attributes for program key (name)

        """
        if key not in self._program_dict:
            msg = f'"{key}" key does not exist. Available keys: '
            for idx, k in enumerate(self._program_dict.keys()):
                if idx > 0:
                    msg += ", "
                msg += f'"{k}"'
            raise KeyError(msg)
        return self._program_dict[key]

    def _target_keys(self, current=False):
        """Get the target keys.

        Parameters
        ----------
        current : bool
            boolean indicating if only current program versions should be
            returned. (default is False)

        Returns
        -------
        keys : list
            list containing program keys (names)

        """
        if current:
            keys = [
                key
                for key in self._program_dict.keys()
                if self._program_dict[key].current
            ]
        else:
            keys = list(self._program_dict.keys())
        return keys

    @staticmethod
    def get_target(key):
        """Get the dictionary for a specified target.

        Parameters
        ----------
        key : str
            Target USGS program that may have a path and an extension

        Returns
        -------
        program_dict : dict
            Dictionary with USGS program attributes for the specified key

        """
        # remove path and extension from key
        key = os.path.basename(key)
        if (
            key.endswith(".exe")
            or key.endswith(".dll")
            or key.endswith(".so")
            or key.endswith(".dylib")
        ):
            key = os.path.splitext(key)[0]

        # return program attributes
        return usgs_program_data()._target_data(key)

    @staticmethod
    def get_keys(current=False):
        """Get target keys from the USGS program database.

        Parameters
        ----------
        current : bool
            If False, all USGS program targets are listed. If True,
            only USGS program targets that are defined as current are
            listed. Default is False.

        Returns
        -------
        keys : list
            list of USGS program targets

        """

        return usgs_program_data()._target_keys(current=current)

    @staticmethod
    def get_program_dict():
        """Get the complete USGS program database.

        Returns
        -------
        program_dict : dict
            Dictionary with USGS program attributes for all targets

        """
        return usgs_program_data()._program_dict

    @staticmethod
    def get_precision(key):
        """Get the dictionary for a specified target.

        Parameters
        ----------
        key : str
            Target USGS program

        Returns
        -------
        precision : list
            List

        """
        target = usgs_program_data().get_target(key)
        precision = []
        if target.standard_switch:
            precision.append("default")
        if target.double_switch:
            precision.append("double")
        return precision

    @staticmethod
    def get_version(key):
        """Get the current version of the specified target.

        Parameters
        ----------
        key : str
            Target USGS program

        Returns
        -------
        version : str
            current version of the specified target

        """
        target = usgs_program_data().get_target(key)
        return target.version

    @staticmethod
    def list_targets(current=False):
        """Print a list of the available USGS program targets.

        Parameters
        ----------
        current : bool
            If False, all USGS program targets are listed. If True,
            only USGS program targets that are defined as current are
            listed. Default is False.

        Returns
        -------

        """
        targets = usgs_program_data()._target_keys(current=current)
        targets.sort()
        msg = "Available targets:\n"
        for idx, target in enumerate(targets):
            msg += f"    {idx + 1:02d} {target}\n"
        print(msg)

        return

    @staticmethod
    def export_json(
        fpth="code.json",
        appdir=None,
        prog_data=None,
        current=False,
        update=True,
        write_markdown=False,
        partial_json=False,
        zip_path=None,
        verbose=False,
    ):
        """Export USGS program data as a json file.

        Parameters
        ----------
        fpth : str
            Path for the json file to be created. Default is "code.json"
        appdir : str
            path for code.json. Overrides code.json path defined in fpth.
            Default is None.
        prog_data : dict
            User-specified program database. If prog_data is None, it will
            be created from the USGS program database
        current : bool
            If False, all USGS program targets are listed. If True,
            only USGS program targets that are defined as current are
            listed. Default is False.
        update : bool
            If True, existing targets in the user-specified program database
            with values in the USGS program database. If False, existing
            targets in the user-specified program database will not be
            updated. Default is True.
        write_markdown : bool
            If True, write markdown file that includes the target name,
            version, and the last-modified date of the download asset (url).
            Default is False.
        partial_json : bool
            Create a partial code.json based on targets in the parent path
            for the code.json file. Default is False.
        zip_path : str
            Zip code.json into zip_path. (default is None)
        verbose : bool
            boolean for verbose output to terminal


        Returns
        -------

        """
        # print a message
        sel = "all of the"
        if prog_data is not None:
            sel = "select"
        elif current:
            sel = "the current"
        print(
            f'writing a json file ("{fpth}") of {sel} USGS programs\n'
            f'in the "{program_data_file}" database.\n'
        )
        if prog_data is not None:
            for idx, key in enumerate(prog_data.keys()):
                print(f"    {idx + 1:>2d}: {key}")

        # process the passed file path into appdir and file_name
        if appdir is None:
            appdir = Path(".")
            file_name = Path(fpth)
            if file_name.parent != str(appdir):
                appdir = file_name.parent
                file_name = file_name.name
            else:
                for idx, argv in enumerate(sys.argv):
                    if argv in ("--appdir", "-ad"):
                        appdir = Path(sys.argv[idx + 1])
        else:
            if isinstance(appdir, str):
                appdir = Path(appdir)
            file_name = Path(fpth).name

        if str(appdir) != ".":
            appdir.mkdir(parents=True, exist_ok=True)

        # get usgs program data
        udata = usgs_program_data.get_program_dict()

        # process the program data
        if prog_data is None:
            if current:
                tdict = {}
                for key, value in udata.items():
                    if value.current:
                        tdict[key] = value
                prog_data = tdict
        # replace existing keys in prog_data with values from
        # same key in usgs_program_data
        else:
            if update:
                ukeys = usgs_program_data.get_keys()
                pkeys = list(prog_data.keys())
                for key in pkeys:
                    if key in ukeys:
                        prog_data[key] = udata[key]

        # update the date of each asset if standard code.json object
        for target, target_dict in prog_data.items():
            if "url" in target_dict.keys():
                url = target_dict["url"]
                header = _request_header(url, verbose=verbose)
                keys = list(header.headers.keys())
                for key in ("Last-Modified", "Date"):
                    if key in keys:
                        url_date = header.headers[key]
                        url_data_obj = datetime.datetime.strptime(
                            url_date, "%a, %d %b %Y %H:%M:%S %Z"
                        )
                        datetime_obj_utc = url_data_obj.replace(
                            tzinfo=datetime.timezone.utc
                        )
                        datetime_str = datetime_obj_utc.strftime("%m/%d/%Y")
                        prog_data[target]["url_download_asset_date"] = datetime_str
                        break

        if partial_json:
            # find targets in appdir
            found_targets = []
            for appdir_file in appdir.iterdir():
                temp_target = appdir_file.stem
                if temp_target.endswith("dbl"):
                    temp_target = temp_target.replace("dbl", "")
                if temp_target in prog_data.keys():
                    if temp_target not in found_targets:
                        found_targets.append(temp_target)

            # determine which targets to remove
            pop_list = []
            for target in prog_data.keys():
                if target not in found_targets:
                    pop_list.append(target)

            # remove unused targets
            for target in pop_list:
                del prog_data[target]

        # update double_switch based on executables in appdir
        for appdir_file in appdir.iterdir():
            temp_target = appdir_file.stem
            if temp_target.endswith("dbl"):
                temp_target = temp_target.replace("dbl", "")
                if temp_target in prog_data.keys():
                    prog_data[temp_target]["double_switch"] = True

        # write code.json to root directory - used by executables CI
        with open(file_name, "w") as file_obj:
            json.dump(prog_data, file_obj, indent=4, sort_keys=True)

        # write code.json if appdir is not the root directory
        if str(appdir) != ".":
            dst = appdir / file_name
            with open(dst, "w") as file_obj:
                json.dump(prog_data, file_obj, indent=4, sort_keys=True)

        # write code.md
        if prog_data is not None and write_markdown:
            sorted_prog_data = {
                key: prog_data[key] for key in sorted(list(prog_data.keys()))
            }
            with open("code.md", "w") as file_obj:
                line = "| Program | Version | UTC Date |"
                file_obj.write(line + "\n")
                line = "| ------- | ------- | ---- |"
                file_obj.write(line + "\n")
                for target, target_dict in sorted_prog_data.items():
                    keys = list(target_dict.keys())
                    line = f"| {target} | {target_dict['version']} |"
                    date_key = "url_download_asset_date"
                    if date_key in keys:
                        line += f" {target_dict[date_key]} |"
                    else:
                        line += " |"
                    line += "\n"
                    file_obj.write(line)

        # zip code.json
        if prog_data is not None and zip_path is not None:
            if verbose:
                print(f"Compressing code.json to zipfile '{Path(zip_path).resolve()}'")
            zip_all(zip_path, dir_pths=appdir, patterns=["code.json"], append=True)

        return

    @staticmethod
    def load_json(fpth="code.json"):
        """Load an existing code json file. Basic error checking is done to
        make sure the file contains the correct keys.

        Parameters
        ----------
        fpth : str
            Path for the json file to be created. Default is "code.json"

        Returns
        -------
        json_dict : dict
            Valid USGS program database

        """
        try:
            with open(fpth, "r") as f:
                json_dict = json.load(f)
            for key, value in json_dict.items():
                json_dict[key] = dotdict(value)
        except:
            json_dict = None

        # check that the json file has valid keys
        msg = f'invalid json format in "{fpth}"'
        if json_dict is not None:
            for key, value in json_dict.items():
                try:
                    for kk in value.keys():
                        if kk not in target_keys:
                            raise KeyError(msg + f' - key ("{kk}")')
                except:
                    raise KeyError(msg)

        return json_dict

    @staticmethod
    def list_json(fpth="code.json"):
        """List an existing code json file.

        Parameters
        ----------
        fpth : str
            Path for the json file to be listed. Default is "code.json"

        Returns
        -------

        """
        json_dict = usgs_program_data.load_json(fpth)

        if json_dict is not None:
            print(f'Data in "{fpth}"')
            for key, value in json_dict.items():
                print(f"  target: {key}")
                for kkey, vvalue in value.items():
                    print(f"    {kkey}: {vvalue}")
        else:
            msg = f'could not load json file "{fpth}".'
            raise OSError(msg)

        # print continuation line
        print("\n")

        return

    @staticmethod
    def update_json(fpth="code.json", temp_dict=None):
        """UPDATE an existing code json file.

        Parameters
        ----------
        fpth : str
            Path for the json file to be listed. Default is "code.json"

        temp_dict : dict
            Dictionary with USGS program data for a target

        Returns
        -------

        """
        if temp_dict is not None:
            if os.path.isfile(fpth):
                json_dict = usgs_program_data.load_json(fpth=fpth)
                if json_dict is not None:
                    for key, value in temp_dict.items():
                        if key not in list(json_dict.keys()):
                            json_dict[key] = value
                    temp_dict = json_dict
            usgs_program_data.export_json(fpth, prog_data=temp_dict)

        return
