import os
import pymake

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

def build_urls():
    pth = os.path.dirname(os.path.abspath(pymake.__file__))
    fpth = os.path.join(pth, 'usgsurls.txt')
    url_in = open(fpth, 'r').read().split('\n')

    urls = {}
    for line in url_in[1:]:
        t = line.split()
        if len(t) < 1:
            continue
        d = {'version': t[1],
             'url': t[2],
             'dirname': t[3],
             'srcdir': t[4]}
        d = dotdict(d)
        urls[t[0]] = d
    urls = dotdict(urls)
    return urls
