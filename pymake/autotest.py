import os
import shutil
import subprocess
import textwrap


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

def setup_comparison(namefile, dst):
    # Construct src pth from namefile
    src = os.path.dirname(namefile)
    action = None
    for root, dirs, files in os.walk(src):
        dl = [d.lower() for d in dirs]
        if '.cmp' in dl:
            idx = dl.index('.cmp')
            if 'mf2005.cmp' in dl:
                action = 'mf2005'
            elif 'mfnwt.cmp' in dl:
                action = 'mfnwt'
            elif 'mfusg.cmp' in dl:
                action = 'mfusg'
            else:
                action = dirs[idx]
            pth = root
            break
    if action is not None:
        dst = os.path.join(dst, '{}'.format(action))
        if not os.path.isdir(dst):
            try:
                os.mkdir(dst)
            except:
                print('Could not make ' + dst)
        files2copy = []
        if action.lower() == '.cmp':
            cmppth = os.path.join(src, action)
            files = os.listdir(cmppth)
            for file in files:
                if '.cmp' in os.path.splitext(file)[1]:
                    files2copy.append(os.path.join(cmppth, file))
            for srcf in files2copy:
                f = os.path.basename(srcf)
                dstf = os.path.join(dst, f)
                # Now copy the file
                if os.path.exists(srcf):
                    print('Copy file from/to ' + srcf + ' ' + dstf)
                    shutil.copy(srcf, dstf)
                else:
                    print(srcf + ' does not exist')
        else:
            i = 12

    return action



def teardown(src):
    if os.path.exists(src):
        print('Removing folder ' + src)
        shutil.rmtree(src)
    return


def run_model(exe_name, namefile, model_ws='./', silent=False, pause=False,
              report=False, normal_msg='normal termination'):
    """
    This method will run the model using subprocess.Popen.

    Parameters
    ----------
    silent : boolean
        Echo run information to screen (default is True).
    pause : boolean, optional
        Pause upon completion (the default is False).
    report : boolean, optional
        Save stdout lines to a list (buff) which is returned
        by the method . (the default is False).

    Returns
    -------
    (success, buff)
    success : boolean
    buff : list of lines of stdout

    """
    success = False
    buff = []

    # Check to make sure that the namefile exists
    if not os.path.isfile(os.path.join(model_ws, namefile)):
        s = 'The namefile for this model does not exists: {}'.format(namefile)
        raise Exception(s)

    proc = subprocess.Popen([exe_name, namefile],
                            stdout=subprocess.PIPE, cwd=model_ws)
    while True:
        line = proc.stdout.readline()
        c = line.decode('utf-8')
        if c != '':
            if normal_msg in c.lower():
                success = True
            c = c.rstrip('\r\n')
            if not silent:
                print('{}'.format(c))
            if report == True:
                buff.append(c)
        else:
            break
    if pause == True:
        input('Press Enter to continue...')
    return [success, buff]


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


def get_namefiles(pth, exclude=None):
    """
    Search through the path (pth) for all .nam files.  Return
    them all in a list.  Namefiles will have paths.

    """
    namefiles = []
    for root, dirs, files in os.walk(pth):
        namefiles += [os.path.join(root, file)
                      for file in files if file.endswith('.nam')]
    if exclude is not None:
        if isinstance(exclude, str):
            exclude = [exclude]
        exclude = [e.lower() for e in exclude]
        pop_list = []
        for namefile in namefiles:
            for e in exclude:
                if e in namefile.lower():
                    pop_list.append(namefile)
        for e in pop_list:
            namefiles.remove(e)

    return namefiles


def get_entries_from_namefile(namefile, ftype=None, unit=None):
    entries = []
    f = open(namefile, 'r')
    for line in f:
        if line.strip() == '':
            continue
        if line[0] == '#':
            continue
        ll = line.strip().split()
        if len(ll) < 3:
            continue
        status = 'UNKNOWN'
        if len(ll) > 3:
            status = ll[3].upper()
        if ftype is not None:
            if ftype.upper() == ll[0].upper():
                filename = os.path.join(os.path.split(namefile)[0], ll[2])
                entries.append((filename, ll[0], ll[1], status))
        elif unit is not None:
            if int(unit) == int(ll[1]):
                filename = os.path.join(os.path.split(namefile)[0], ll[2])
                entries.append((filename, ll[0], ll[1], status))
    f.close()
    if len(entries) < 1:
        entries.append((None, None, None, None))
    return entries


def get_sim_name(namefiles, rootpth=None):
    if isinstance(namefiles, str):
        namefiles = [namefiles]
    sim_name = []
    for namefile in namefiles:
        t = namefile.split(os.sep)
        if rootpth is None:
            idx = -1
        else:
            idx = t.index(os.path.split(rootpth)[1])
        dst = ''
        # build dst with everything after the rootpth and before
        # the namefile file name.
        if idx < len(t):
            for d in t[idx + 1:-1]:
                dst += '{}_'.format(d)
        # add namefile basename without extension
        dst += t[-1].replace('.nam', '')
        sim_name.append(dst)
    return sim_name


def compare_budget(namefile1, namefile2, max_cumpd=0.01, max_incpd=0.01,
                   outfile=None):
    """
    Compare the results from these two simulations.

    """
    import numpy as np
    import flopy

    # headers
    headers = ('INCREMENTAL', 'CUMULATIVE')
    dir = ('IN', 'OUT')

    # Get name of list files
    list = get_entries_from_namefile(namefile1, 'list')
    list1 = list[0][0]
    list2 = get_entries_from_namefile(namefile2, 'list')
    list2 = list[0][0]

    # Open output file
    if outfile is not None:
        f = open(outfile, 'w')
        f.write('Created by pymake.autotest.compare\n')

    # Get numpy budget tables for list1
    lstobj = flopy.utils.MfusgListBudget(list1)
    lst1 = []
    lst1.append(lstobj.get_incremental())
    lst1.append(lstobj.get_cumulative())

    # Get numpy budget tables for list2
    lstobj = flopy.utils.MfusgListBudget(list2)
    lst2 = []
    lst2.append(lstobj.get_incremental())
    lst2.append(lstobj.get_cumulative())

    icnt = 0
    v0 = np.zeros(2, dtype=np.float)
    v1 = np.zeros(2, dtype=np.float)
    err = np.zeros(2, dtype=np.float)

    # Process cumulative and incremental
    for idx in range(2):
        if idx > 0:
            max_pd = max_cumpd
        else:
            max_pd = max_incpd
        kper = lst1[idx]['stress_period']
        kstp = lst1[idx]['time_step']

        # Process each time step
        for jdx in range(kper.shape[0]):

            err[:] = 0.
            t0 = lst1[idx][jdx]
            t1 = lst2[idx][jdx]

            if outfile is not None:

                maxcolname = 0
                for colname in t0.dtype.names:
                    maxcolname = max(maxcolname, len(colname))

                s = 2 * '\n'
                s += 'STRESS PERIOD: {} TIME STEP: {}'.format(kper[jdx] + 1,
                                                                kstp[jdx] + 1)
                f.write(s)

                if idx == 0:
                    f.write('\nINCREMENTAL BUDGET\n')
                else:
                    f.write('\nCUMULATIVE BUDGET\n')

                for i, colname in enumerate(t0.dtype.names):
                    if i == 0:
                        s = '{:<21} {:>21} {:>21} {:>21}\n'.format('Budget Entry',
                                                              'Model 1',
                                                              'Model 2',
                                                              'Difference')
                        f.write(s)
                        s = 87 * '-' + '\n'
                        f.write(s)
                    diff = t0[colname] - t1[colname]
                    s = '{:<21} {:>21} {:>21} {:>21}\n'.format(colname,
                                                               t0[colname],
                                                               t1[colname],
                                                               diff)
                    f.write(s)

            v0[0] = t0['TOTAL_IN']
            v1[0] = t1['TOTAL_IN']
            if v0[0] > 0.:
                err[0] = 100. * (v1[0] - v0[0]) / v0[0]
            v0[1] = t0['TOTAL_OUT']
            v1[1] = t1['TOTAL_OUT']
            if v0[1] > 0.:
                err[1] = 100. * (v1[1] - v0[1]) / v0[1]
            for kdx, t in enumerate(err):
                if abs(t) > max_pd:
                    icnt += 1
                    e = '"{} {}" percent difference ({})'.format(headers[idx], dir[kdx], t) + \
                        ' for stress period {} and time step {} > {}.'.format(kper[jdx]+1, kstp[jdx]+1, max_pd) + \
                        ' Reference value = {}. Simulated value = {}.'.format(v0[kdx], v1[kdx])
                    e = textwrap.fill(e, width=70, initial_indent='    ', subsequent_indent='    ')
                    f.write('{}\n'.format(e))
                    f.write('\n')

    # Close output file
    if outfile is not None:
        f.close()


    # test for failure
    success = True
    if icnt > 0:
        success = False
    return success



def compare_heads(namefile1, namefile2, precision='single',
                  htol=0.001, outfile=None):
    """
    Compare the results from these two simulations.

    """
    import flopy

    dbs = 'DATA(BINARY)'

    # Get oc info, and return if OC not included in models
    ocf1 = get_entries_from_namefile(namefile1, 'OC')
    ocf2 = get_entries_from_namefile(namefile2, 'OC')
    if ocf1[0][0] is None or ocf2[0][0] is None:
        return True

    # Get head info for namefile1
    hu1, hfpth1, du1, dfpth1 = flopy.modflow.ModflowOc.get_ocoutput_units(ocf1[0][0])
    if hu1 != 0:
        entries = get_entries_from_namefile(namefile1, unit=abs(hu1))
        hfpth1, status1 = entries[0][0], entries[0][1]

    # Get head info for namefile2
    hu2, hfpth2, du2, dfpth2 = flopy.modflow.ModflowOc.get_ocoutput_units(ocf2[0][0])
    if hu2 != 0:
        entries = get_entries_from_namefile(namefile2, unit=abs(hu2))
        hfpth2, status2 = entries[0][0], entries[0][1]

    if hfpth1 is None or hfpth2 is None:
        return True

    if not os.path.isfile(hfpth1) or not os.path.isfile(hfpth2):
        return True

    # Open output file
    if outfile is not None:
        f = open(outfile, 'w')
        f.write('Created by pymake.autotest.compare\n')

    # Get head objects
    status1 = status1.upper()
    if status1 == dbs:
        headobj1 = flopy.utils.HeadFile(hfpth1, precision=precision)
    else:
        headobj1 = flopy.utils.FormattedHeadFile(hfpth1)

    status2 = status2.upper()
    if status2 == dbs:
        headobj2 = flopy.utils.HeadFile(hfpth2, precision=precision)
    else:
        headobj2 = flopy.utils.FormattedHeadFile(hfpth2)

    # get times
    times1 = headobj1.get_times()
    times2 = headobj2.get_times()

    assert times1 == times2, 'times in two head files are not equal'

    kstpkper = headobj1.get_kstpkper()

    header = '{:>15s} {:>15s} {:>15s}\n'.format(' ', ' ', 'MAXIMUM') + \
             '{:>15s} {:>15s} {:>15s}\n'.format('STRESS PERIOD', 'TIME STEP', 'HEAD DIFFERENCE') + \
             '{0:>15s} {0:>15s} {0:>15s}\n'.format(15*'-')

    icnt = 0
    # Process cumulative and incremental
    for idx, time in enumerate(times1):
        h1 = headobj1.get_data(totim=time)
        h2 = headobj2.get_data(totim=time)

        diffmax, indices = calculate_difference(h1, h2)

        if idx < 1:
            f.write(header)
        f.write('{:15d} {:15d} {:15.6g}\n'.format(kstpkper[idx][1]+1, kstpkper[idx][0]+1, diffmax))

        if diffmax >= htol:
            icnt += 1
            e = 'Maximum head difference ({}) exceeds {} at node location(s):\n'.format(diffmax, htol)
            e = textwrap.fill(e, width=70, initial_indent='  ', subsequent_indent='  ')
            f.write('{}\n'.format(e))
            e = ''
            for itupe in indices:
                for ind in itupe:
                    e += '{} '.format(ind)
            e = textwrap.fill(e, width=70, initial_indent='    ', subsequent_indent='    ')
            f.write('{}\n'.format(e))
            f.write('\n{}'.format(header))

    # Close output file
    if outfile is not None:
        f.close()

    # test for failure
    success = True
    if icnt > 0:
        success = False
    return success


def calculate_difference(v1, v2):
    import numpy as np
    # For a usg simulation, the row and column are switched in the binary
    # head file.
    nl1, nr1, nc1 = v1.shape
    nl2, nr2, nc2 = v2.shape
    if nl1 == nl2 and nr1 == nc2 and nc1 == nr2:
        v1 = v1.flatten()
        v2 = v2.flatten()

    diff = abs(v1 - v2)
    diffmax = diff.max()
    indices = np.where(diff == diffmax)
    return diffmax, indices


def compare(namefile1, namefile2, precision='single',
            max_cumpd=0.01, max_incpd=0.01, htol=0.001,
            outfile1=None, outfile2=None):

    """
    Compare the results from two simulations
    """

    # Compare budgets from the list files in namefile1 and namefile2
    success1 = compare_budget(namefile1, namefile2,
                              max_cumpd=max_cumpd, max_incpd=max_incpd,
                              outfile=outfile1)
    success2 = compare_heads(namefile1, namefile2, precision=precision,
                             htol=htol, outfile=outfile2)
    success = False
    if success1 and success2:
        success = True
    return success

