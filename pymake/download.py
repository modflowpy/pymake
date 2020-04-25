from __future__ import print_function

import os
from zipfile import ZipFile, ZipInfo
import tarfile


class MyZipFile(ZipFile):
    """
    ZipFile file attributes are not being preserved.  This preserves file
    attributes as described here
    https://stackoverflow.com/questions/39296101/python-zipfile-removes-execute-permissions-from-binaries

    """

    def extract(self, member, path=None, pwd=None):
        if not isinstance(member, ZipInfo):
            member = self.getinfo(member)

        if path is None:
            path = os.getcwd()

        ret_val = self._extract_member(member, path, pwd)
        attr = member.external_attr >> 16
        if attr != 0:
            os.chmod(ret_val, attr)
        return ret_val

    def extractall(self, path=None, members=None, pwd=None):
        if members is None:
            members = self.namelist()

        if path is None:
            path = os.getcwd()
        else:
            if hasattr(os, 'fspath'):
                # introduced in python 3.6 and above
                path = os.fspath(path)

        for zipinfo in members:
            self.extract(zipinfo, path, pwd)


def download_and_unzip(url, pth='./', delete_zip=True, verify=True,
                       timeout=30, nattempts=10, chunk_size=204800):
    try:
        import requests
    except Exception as e:
        msg = "pymake.download_and_unzip() error import requests: " + \
              str(e)
        raise Exception(msg)
    if not os.path.exists(pth):
        print('Creating the directory:\n    {}'.format(pth))
        os.makedirs(pth)
    print('Attempting to download the file:\n    {}'.format(url))
    file_name = os.path.join(pth, url.split('/')[-1])
    # download the file
    success = False
    for idx in range(nattempts):
        print(' download attempt: {}'.format(idx + 1))
        #
        req = requests.get(url, stream=True, verify=verify)
        fs = 0
        lenfs = 0
        if 'Content-length' in req.headers:
            fs = req.headers['Content-length']
            lenfs = len(fs)
            fs = int(fs)
        if fs > 0:
            bfmt = '{:' + '{}'.format(lenfs) + ',d}'
            sbfmt = '{:>' + '{}'.format(len(bfmt.format(int(fs)))) + 's} bytes'
            print(
                '   file size: {}'.format(sbfmt.format(bfmt.format(int(fs)))))
        ds = 0
        try:
            req = requests.get(url, verify=verify, timeout=timeout)
            with open(file_name, 'wb') as f:
                for chunk in req.iter_content(chunk_size=chunk_size):
                    if chunk:
                        ds += len(chunk)
                        msg = '     downloaded ' + \
                              sbfmt.format(bfmt.format(ds)) + \
                              ' of ' + bfmt.format(int(fs)) + ' bytes' + \
                              ' ({:10.4%})'.format(float(ds) / float(fs))
                        print(msg)
                        f.write(chunk)
            success = True
        except:
            if idx + 1 == nattempts:
                msg = 'Cannot download file:\n    {}'.format(url)
                raise Exception(msg)
        if success:
            break

    # Unzip the file, and delete zip file if successful.
    if 'zip' in os.path.basename(file_name) or \
            'exe' in os.path.basename(file_name):
        z = MyZipFile(file_name)
        try:
            print('Extracting the zipfile...')
            z.extractall(pth)
        except:
            p = 'Could not unzip the file.  Stopping.'
            raise Exception(p)
        z.close()
    elif 'tar' in os.path.basename(file_name):
        ar = tarfile.open(file_name)
        ar.extractall(path=pth)
        ar.close()

    # delete the zipfile
    if delete_zip:
        print('Deleting the zipfile...')
        os.remove(file_name)
    print('Done downloading and extracting...\n')
