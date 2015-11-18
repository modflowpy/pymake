import os
import shutil

ignore_ext = ['.hds', '.hed', '.bud', '.cbb', '.cbc',
              '.ddn', '.ucn', '.glo', '.lst', '.list',
              '.gwv', '.mv']

def setup(namefile, dst):

    # Construct src pth from namefile
    src = os.path.dirname(namefile)

    # Create the destination folder
    if os.path.exists(dst):
        print('Removing folder ' + dst)
        shutil.rmtree(dst)
    os.mkdir(dst)

    # Make list of files to copy
    fname = os.path.abspath(namefile)
    nf = os.path.basename(namefile)
    files2copy = [nf] + get_input_files(fname)

    # Copy the files
    for f in files2copy:
        srcf = os.path.join(src, f)
        dstf = os.path.join(dst, f)

        # Check to see if dstf is going into a subfolder, and create that
        # subfolder if it doesn't exist
        sf = os.path.dirname(dstf)
        if not os.path.isdir(sf):
            try:
                os.mkdir(sf)
            except:
                print('Could not make ' + sf)

        # Now copy the file
        if os.path.exists(srcf):
            print('Copy file from/to ' + srcf + ' ' + dstf)
            shutil.copy(srcf, dstf)
        else:
            print(srcf + ' does not exist')

    return

def teardown(src):
    if os.path.exists(src):
        print('Removing folder ' + src)
        shutil.rmtree(src)
    return


def get_input_files(namefile):
    """
    Return a list of all the input files in this model

    """

    srcdir = os.path.dirname(namefile)
    filelist = []
    fname = os.path.join(srcdir, namefile)
    with open(fname, 'r') as f:
        lines = f.readlines()

    for line in lines:
        ll = line.strip().split()
        if len(ll) < 2:
            continue
        if line.strip()[0] in ['#', '!']:
            continue
        ext = os.path.splitext(ll[2])[1]
        if ext.lower() not in ignore_ext:
            if len(ll) > 3:
                if 'replace' in ll[3].lower():
                    continue
            filelist.append(ll[2])

    # Now go through every file and look for other files to copy,
    # such as 'OPEN/CLOSE'.  If found, then add that file to the
    # list of files to copy.
    otherfiles = []
    for fname in filelist:
        fname = os.path.join(srcdir, fname)
        try:
            f = open(fname, 'r')
            for line in f:

                # Skip invalid lines
                ll = line.strip().split()
                if len(ll) < 2:
                    continue
                if line.strip()[0] in ['#', '!']:
                    continue

                if 'OPEN/CLOSE' in line.upper():
                    for i, s in enumerate(ll):
                        if s.upper() == 'OPEN/CLOSE':
                            stmp = ll[i + 1]
                            stmp = stmp.replace('"', '')
                            stmp = stmp.replace("'", '')
                            otherfiles.append(stmp)
                            break
        except:
            print(fname + ' does not exist')

    filelist = filelist + otherfiles

    return filelist