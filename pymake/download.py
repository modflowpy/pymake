from __future__ import print_function

import os
from zipfile import ZipFile
import tarfile

try:
    # For Python 3.0 and later
    from urllib.request import urlretrieve
except ImportError:
    # Fall back to Python 2's urllib
    from urllib import urlretrieve


def download_and_unzip(url, pth='./', delete_zip=True, verify=True,
                       timeout=30, nattempts=10):
    try:
        import requests
    except Exception as e:
        msg = "pymake.download_and_unzip() error import requests: " + \
              str(e)
        raise Exception(msg)
    if not os.path.exists(pth):
        print('Creating the directory: {}'.format(pth))
        os.makedirs(pth)
    print('Attempting to download the file: ', url)
    file_name = os.path.join(pth, url.split('/')[-1])
    success = False
    for idx in range(nattempts):
        print(' download attempt: {}'.format(idx + 1))
        try:
            req = requests.get(url, verify=verify, timeout=timeout)
            f = open(file_name, 'wb')
            for chunk in req.iter_content(100000):
                f.write(chunk)
            f.close()
            success = True
        except:
            if idx + 1 == nattempts:
                msg = 'Cannot download file: {}'.format(url)
                raise Exception(msg)
        if success:
            break
    # ierr = 0
    # try:
    #     f, header = urlretrieve(url, file_name)
    # except:
    #     if 'exe' in os.path.basename(file_name).lower():
    #         try:
    #             import requests
    #         except Exception as e:
    #             msg = "pymake.download_and_unzip() error import requests: " + \
    #                   str(e)
    #             raise Exception(msg)
    #         try:
    #             req = requests.get(url, verify=verify)
    #             f = open(file_name, 'wb')
    #             for chunk in req.iter_content(100000):
    #                 f.write(chunk)
    #             f.close()
    #         except:
    #             ierr = 1
    #     else:
    #         ierr = 1
    #     if ierr != 0:
    #         msg = 'Cannot download file: {}'.format(url)
    #         raise Exception(msg)

    # Unzip the file, and delete zip file if successful.
    if 'zip' in os.path.basename(file_name) or \
                    'exe' in os.path.basename(file_name):
        z = ZipFile(file_name)
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
    if delete_zip:
        print('Deleting the zipfile...')
        os.remove(file_name)
    print('Done downloading and extracting...')
