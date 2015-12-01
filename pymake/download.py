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

def download_and_unzip(url, pth='./'):
    if not os.path.exists(pth):
        print('Creating the directory: {}'.format(pth))
        os.makedirs(pth)
    print('Attempting to download the file: ', url)
    file_name = os.path.join(pth, url.split('/')[-1])
    try:
        f, header = urlretrieve(url, file_name)
    except:
        msg = 'Cannot download file: {}'.format(url)
        raise Exception(msg)

    # Unzip the file, and delete zip file if successful.
    if 'zip' in os.path.basename(file_name) or 'exe' in os.path.basename(file_name):
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
    print('Deleting the zipfile...')
    os.remove(file_name)
    print('Done downloading and extracting...')
