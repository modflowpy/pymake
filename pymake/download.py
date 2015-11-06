from __future__ import print_function

import os
from zipfile import ZipFile
try:
    # For Python 3.0 and later
    from urllib.request import urlretrieve
except ImportError:
    # Fall back to Python 2's urllib
    from urllib import urlretrieve

def download_and_unzip(url, pth='./'):
    print('Attempting to download the file: ', url)
    file_name = os.path.join(pth, url.split('/')[-1])
    try:
        urlretrieve(url, file_name)
    except:
        print('Error.  Cannot download the file.')
        raise Exception()

    # Unzip the file, and delete zip file if successful.
    z = ZipFile(file_name)
    try:
        print('Extracting the zipfile...')
        z.extractall(pth)
    except:
        p = 'Could not unzip the file.  Stopping.'
        raise Exception(p)
    z.close()
    print('Deleting the zipfile...')
    os.remove(file_name)
    print('Done downloading and extracting...')
