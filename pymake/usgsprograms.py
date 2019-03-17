import os
import json
import pymake


class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


# data file containing the USGS program data
program_data_file = 'usgsprograms.txt'

# keys to create for each target
target_keys = ['version', 'current', 'url', 'dirname', 'srcdir']

def str_to_bool(s):
    if s == 'True':
        return True
    elif s == 'False':
        return False
    else:
        msg = 'Invalid string passed - "{}"'.format(s)
        raise ValueError(msg)


class usgs_program_data:
    def __init__(self):
        self._program_dict = self._build_urls()

    def _build_urls(self):
        pth = os.path.dirname(os.path.abspath(pymake.__file__))
        fpth = os.path.join(pth, program_data_file)
        url_in = open(fpth, 'r').read().split('\n')

        urls = {}
        for line in url_in[1:]:
            t = line.split()
            if len(t) < 1:
                continue
            # programatically build a dictionary for each target
            d = {}
            for idx, key in enumerate(target_keys):
                v = t[idx+1]
                if key == 'current':
                    v = str_to_bool(v)
                d[key] = v

            # make it possible to access each key with a dot (.)
            d = dotdict(d)
            urls[t[0]] = d
        return dotdict(urls)

    def get_target_data(self, key):
        if key not in self._program_dict:
            msg = '"{}" key does not exist. Available keys: '.format(key)
            for idx, k in enumerate(self._program_dict.keys()):
                if idx > 0:
                    msg += ', '
                msg += '"{}"'.format(k)
            raise KeyError(msg)
        return self._program_dict[key]

    def get_target_keys(self, current=False):
        if current:
            keys = [key for key in self._program_dict.keys()
                    if self._program_dict[key].current]
        else:
            keys = list(self._program_dict.keys())
        return keys

    def get_program_dict(self):
        return self._program_dict

    @staticmethod
    def get_target(key):
        return usgs_program_data().get_target_data(key)

    @staticmethod
    def get_keys(current=False):
        return usgs_program_data().get_target_keys(current=current)

    @staticmethod
    def list_targets(current=False):
        targets = usgs_program_data().get_target_keys(current=current)
        targets.sort()
        msg = 'Available targets:\n'
        for idx, target in enumerate(targets):
            msg += '    {:02d} {}\n'.format(idx + 1, target)
        print(msg)

        return

    @staticmethod
    def export_json(fpth='code.json', prog_data=None, current=False):
        # print a message
        sel = 'all of the'
        if prog_data is not None:
            sel = 'select'
        elif current:
            sel = 'the current'
        print('writing a json file ("{}") '.format(fpth) +
              'of {} USGS programs\n'.format(sel) +
              'in the "{}" database.'.format(program_data_file))
        if prog_data is not None:
            for idx, key in enumerate(prog_data.keys()):
                print('    {:>2d}: {}'.format(idx + 1, key))
        print('\n')

        # process the program data
        if prog_data is None:
            prog_data = usgs_program_data().get_program_dict()
            if current:
                tdict = {}
                for key, value in prog_data.items():
                    if value.current:
                        tdict[key] = value
                prog_data = tdict

        # export file
        with open(fpth, 'w') as f:
            json.dump(prog_data, f, indent=4)

    @staticmethod
    def load_json(fpth='code.json'):
        try:
            with open(fpth, 'r') as f:
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
