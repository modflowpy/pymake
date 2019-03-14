import os
import pymake


class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

def str_to_bool(s):
    if s == 'True':
        return True
    elif s == 'False':
        return False
    else:
        msg = 'Invalid string passed - "{}"'.format(s)
        raise ValueError(msg)

class usgs_prog_data:
    def __init__(self):
        self._url_dict = self._build_urls()

    def _build_urls(self):
        pth = os.path.dirname(os.path.abspath(pymake.__file__))
        fpth = os.path.join(pth, 'usgsurls.txt')
        url_in = open(fpth, 'r').read().split('\n')

        urls = {}
        for line in url_in[1:]:
            t = line.split()
            if len(t) < 1:
                continue
            d = {'version': t[1],
                 'current': str_to_bool(t[2]),
                 'url': t[3],
                 'dirname': t[4],
                 'srcdir': t[5]}
            d = dotdict(d)
            urls[t[0]] = d
        return dotdict(urls)

    def get_target_data(self, key):
        if key not in self._url_dict:
            msg = '"{}" key does not exist. Available keys: '.format(key)
            for idx, k in enumerate(self._url_dict.keys()):
                if idx > 0:
                    msg += ', '
                msg += '"{}"'.format(k)
            raise KeyError(msg)
        return self._url_dict[key]

    def get_target_keys(self, current=False):
        if current:
            keys = [key for key in self._url_dict.keys()
                    if self._url_dict[key].current]
        else:
            keys = list(self._url_dict.keys())
        return keys

    @staticmethod
    def get_target(key):
        return usgs_prog_data().get_target_data(key)

    @staticmethod
    def get_keys(current=False):
        return usgs_prog_data().get_target_keys(current=current)

    @staticmethod
    def list_targets(current=False):
        targets = usgs_prog_data().get_target_keys(current=current)
        targets.sort()
        msg = 'Available targets:\n'
        for idx, target in enumerate(targets):
            msg += '    {:02d} {}\n'.format(idx+1, target)
        print(msg)

        return
