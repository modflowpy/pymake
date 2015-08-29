import urllib2
from zipfile import ZipFile
import os

def download_and_unzip(url):
    print 'Attemping to download the file: ', url
    file_name = url.split('/')[-1]
    try:
        u = urllib2.urlopen(url)
    except:
        print ('Error.  Cannot download the file.')
        raise Exception()
    f = open(file_name, 'wb')
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])

    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break

        file_size_dl += len(buffer)
        f.write(buffer)
        # status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        # status = status + chr(8)*(len(status)+1)

    f.close()

    #Unzip the file, and delete zip file if successful.
    z = ZipFile(file_name)
    try:
        z.extractall('./')
    except:
        print 'Could not unzip the file.  Stopping.'
        raise Exception()
    z.close()
    print 'Deleting the zipfile...'
    os.remove(file_name)
    print 'Done downloading and extracting...'

