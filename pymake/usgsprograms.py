import os
import sys
import json
from collections import OrderedDict


class dotdict(dict):
    """dot.notation access to dictionary attributes."""

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


# data file containing the USGS program data
program_data_file = "usgsprograms.txt"

# keys to create for each target
target_keys = [
    "version",
    "current",
    "url",
    "dirname",
    "srcdir",
    "standard_switch",
    "double_switch",
]


def str_to_bool(s):
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
        msg = 'Invalid string passed - "{}"'.format(s)
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

        program_data = OrderedDict()
        for line in url_in[1:]:
            t = line.split()
            if len(t) < 1:
                continue
            # programmatically build a dictionary for each target
            d = OrderedDict()
            for idx, key in enumerate(target_keys):
                v = t[idx + 1]
                if key in ["current", "standard_switch", "double_switch"]:
                    v = str_to_bool(v)
                d[key] = v

            # make it possible to access each key with a dot (.)
            d = dotdict(d)
            program_data[t[0]] = d

        return dotdict(program_data)

    def _target_data(self, key):
        """Get the dictionary for the target key."""
        if key not in self._program_dict:
            msg = '"{}" key does not exist. Available keys: '.format(key)
            for idx, k in enumerate(self._program_dict.keys()):
                if idx > 0:
                    msg += ", "
                msg += '"{}"'.format(k)
            raise KeyError(msg)
        return self._program_dict[key]

    def _target_keys(self, current=False):
        """Get the target keys."""
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
        if key.endswith(".exe") or key.endswith(".dll") or key.endswith(".so"):
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
            precision.append(False)
        if target.double_switch:
            precision.append(True)
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
            msg += "    {:02d} {}\n".format(idx + 1, target)
        print(msg)

        return

    @staticmethod
    def export_json(
        fpth="code.json", prog_data=None, current=False, update=True
    ):
        """Export USGS program data as a json file.

        Parameters
        ----------
        fpth : str
            Path for the json file to be created. Default is "code.json"
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
            'writing a json file ("{}") '.format(fpth)
            + "of {} USGS programs\n".format(sel)
            + 'in the "{}" database.'.format(program_data_file)
        )
        if prog_data is not None:
            for idx, key in enumerate(prog_data.keys()):
                print("    {:>2d}: {}".format(idx + 1, key))
        print("\n")

        # get usgs program data
        udata = usgs_program_data.get_program_dict()

        # process the program data
        if prog_data is None:
            if current:
                tdict = OrderedDict()
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

        # export file
        try:
            with open(fpth, "w") as f:
                json.dump(prog_data, f, indent=4)
        except:
            msg = 'could not export json file "{}"'.format(fpth)
            raise IOError(msg)

        # export code.json to --appdir directory, if the
        # command line argument was specified. Only done if not travis
        appdir = "."
        for idx, argv in enumerate(sys.argv):
            if argv in ("--appdir", "-ad"):
                appdir = sys.argv[idx + 1]

        # make appdir if it does not already exist
        if not os.path.isdir(appdir):
            os.makedirs(appdir)

        # write code.json
        if appdir != ".":
            dst = os.path.join(appdir, fpth)
            with open(dst, "w") as f:
                json.dump(prog_data, f, indent=4)

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
        msg = 'invalid json format in "{}"'.format(fpth)
        if json_dict is not None:
            for key, value in json_dict.items():
                try:
                    for kk in value.keys():
                        if kk not in target_keys:
                            raise KeyError(msg)
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
            print('Data in "{}"'.format(fpth))
            for key, value in json_dict.items():
                print("  target: {}".format(key))
                for kkey, vvalue in value.items():
                    print("    {}: {}".format(kkey, vvalue))
        else:
            msg = 'could not load json file "{}".'.format(fpth)
            raise IOError(msg)

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
