import os
import shutil
import subprocess
import textwrap

ignore_ext = ['.hds', '.hed', '.bud', '.cbb', '.cbc',
              '.ddn', '.ucn', '.glo', '.lst', '.list',
              '.gwv', '.mv', '.out']


def setup(namefile, dst, remove_existing=True):
    # Construct src pth from namefile
    src = os.path.dirname(namefile)

    # Create the destination folder, if required
    create_dir = False
    if os.path.exists(dst):
        if remove_existing:
            print('Removing folder ' + dst)
            shutil.rmtree(dst)
            create_dir = True
    else:
        create_dir = True
    if create_dir:
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


def setup_comparison(namefile, dst, remove_existing=True):
    # Construct src pth from namefile
    src = os.path.dirname(namefile)
    action = None
    for root, dirs, files in os.walk(src):
        dl = [d.lower() for d in dirs]
        if any('.cmp' in s for s in dl):
            idx = None
            for jdx, d in enumerate(dl):
                if '.cmp' in d:
                    idx = jdx
                    break
            if idx is not None:
                if 'mf2005.cmp' in dl[idx]:
                    action = dirs[idx]
                elif 'mfnwt.cmp' in dl[idx]:
                    action = dirs[idx]
                elif 'mfusg.cmp' in dl[idx]:
                    action = dirs[idx]
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
        cmppth = os.path.join(src, action)
        files = os.listdir(cmppth)
        files2copy = []
        if action.lower() == '.cmp':
            for file in files:
                if '.cmp' in os.path.splitext(file)[1].lower():
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
            for file in files:
                if '.nam' in os.path.splitext(file)[1].lower():
                    files2copy.append(
                            os.path.join(cmppth, os.path.basename(file)))
                    nf = os.path.join(src, action, os.path.basename(file))
                    setup(nf, dst, remove_existing=remove_existing)
                    break

    return action


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
                        if 'OPEN/CLOSE' in s.upper():
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


def get_entries_from_namefile(namefile, ftype=None, unit=None, extension=None):
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
        elif extension is not None:
            filename = os.path.join(os.path.split(namefile)[0], ll[2])
            ext = os.path.splitext(filename)[1]
            if len(ext) > 0:
                if ext[0] == '.':
                    ext = ext[1:]
                if extension.lower() == ext.lower():
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
                   outfile=None, files1=None, files2=None):
    """
    Compare the results from these two simulations.

    """
    import numpy as np
    import flopy

    # headers
    headers = ('INCREMENTAL', 'CUMULATIVE')
    dir = ('IN', 'OUT')

    # Get name of list files
    list1 = None
    if files1 is None:
        list = get_entries_from_namefile(namefile1, 'list')
        list1 = list[0][0]
    else:
        for file in files1:
            if 'list' in os.path.basename(
                    file).lower() or 'lst' in os.path.basename(file).lower():
                list1 = file
                break
    list2 = None
    if files2 is None:
        list = get_entries_from_namefile(namefile2, 'list')
        list2 = list[0][0]
    else:
        for file in files2:
            if 'list' in os.path.basename(
                    file).lower() or 'lst' in os.path.basename(file).lower():
                list2 = file
                break
    # Determine if there are two files to compare
    if list1 is None or list2 is None:
        return True

    # Open output file
    if outfile is not None:
        f = open(outfile, 'w')
        f.write('Created by pymake.autotest.compare\n')

    # Initialize SWR budget objects
    lst1obj = flopy.utils.MfusgListBudget(list1)
    lst2obj = flopy.utils.MfusgListBudget(list2)

    # Determine if there any SWR entries in the budget file
    if not lst1obj.isvalid() or not lst2obj.isvalid():
        return True

    # Get numpy budget tables for list1
    lst1 = []
    lst1.append(lst1obj.get_incremental())
    lst1.append(lst1obj.get_cumulative())

    # Get numpy budget tables for list2
    lst2 = []
    lst2.append(lst2obj.get_incremental())
    lst2.append(lst2obj.get_cumulative())

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
                        s = '{:<21} {:>21} {:>21} {:>21}\n'.format(
                                'Budget Entry',
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
                    e = '"{} {}" percent difference ({})'.format(headers[idx],
                                                                 dir[kdx], t) + \
                        ' for stress period {} and time step {} > {}.'.format(
                                kper[jdx] + 1, kstp[jdx] + 1, max_pd) + \
                        ' Reference value = {}. Simulated value = {}.'.format(
                                v0[kdx], v1[kdx])
                    e = textwrap.fill(e, width=70, initial_indent='    ',
                                      subsequent_indent='    ')
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


def compare_swrbudget(namefile1, namefile2, max_cumpd=0.01, max_incpd=0.01,
                      outfile=None, files1=None, files2=None):
    """
    Compare the results from these two simulations.

    """
    import numpy as np
    import flopy

    # headers
    headers = ('INCREMENTAL', 'CUMULATIVE')
    dir = ('IN', 'OUT')

    # Get name of list files
    list1 = None
    if files1 is None:
        lst = get_entries_from_namefile(namefile1, 'list')
        list1 = lst[0][0]
    else:
        for file in files1:
            if 'list' in os.path.basename(
                    file).lower() or 'lst' in os.path.basename(file).lower():
                list1 = file
                break
    list2 = None
    if files2 is None:
        lst = get_entries_from_namefile(namefile2, 'list')
        list2 = lst[0][0]
    else:
        for file in files2:
            if 'list' in os.path.basename(
                    file).lower() or 'lst' in os.path.basename(file).lower():
                list2 = file
                break
    # Determine if there are two files to compare
    if list1 is None or list2 is None:
        return True

    # Initialize SWR budget objects
    lst1obj = flopy.utils.SwrListBudget(list1)
    lst2obj = flopy.utils.SwrListBudget(list2)

    # Determine if there any SWR entries in the budget file
    if not lst1obj.isvalid() or not lst2obj.isvalid():
        return True

    # Get numpy budget tables for list1
    lst1 = []
    lst1.append(lst1obj.get_incremental())
    lst1.append(lst1obj.get_cumulative())

    # Get numpy budget tables for list2
    lst2 = []
    lst2.append(lst2obj.get_incremental())
    lst2.append(lst2obj.get_cumulative())

    icnt = 0
    v0 = np.zeros(2, dtype=np.float)
    v1 = np.zeros(2, dtype=np.float)
    err = np.zeros(2, dtype=np.float)

    # Open output file
    if outfile is not None:
        f = open(outfile, 'w')
        f.write('Created by pymake.autotest.compare\n')

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
                        s = '{:<21} {:>21} {:>21} {:>21}\n'.format(
                                'Budget Entry',
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
                    e = '"{} {}" percent difference ({})'.format(headers[idx],
                                                                 dir[kdx], t) + \
                        ' for stress period {} and time step {} > {}.'.format(
                                kper[jdx] + 1, kstp[jdx] + 1, max_pd) + \
                        ' Reference value = {}. Simulated value = {}.'.format(
                                v0[kdx], v1[kdx])
                    e = textwrap.fill(e, width=70, initial_indent='    ',
                                      subsequent_indent='    ')
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
                  htol=0.001, outfile=None, files1=None, files2=None,
                  difftol=False):
    """
    Compare the results from these two simulations.

    """
    import flopy

    dbs = 'DATA(BINARY)'

    # Get head info for namefile1
    hfpth1 = None
    status1 = dbs
    if files1 is None:
        # Get oc info, and return if OC not included in models
        ocf1 = get_entries_from_namefile(namefile1, 'OC')
        if ocf1[0][0] is None:
            return True

        hu1, hfpth1, du1, dfpth1 = flopy.modflow.ModflowOc.get_ocoutput_units(
                ocf1[0][0])
        if hu1 != 0:
            entries = get_entries_from_namefile(namefile1, unit=abs(hu1))
            hfpth1, status1 = entries[0][0], entries[0][1]
    else:
        if isinstance(files1, str):
            files1 = [files1]
        for file in files1:
            if 'hds' in os.path.basename(
                    file).lower() or 'hed' in os.path.basename(file).lower():
                hfpth1 = file
                break

    # Get head info for namefile2
    hfpth2 = None
    status2 = dbs
    if files2 is None:
        # Get oc info, and return if OC not included in models
        ocf2 = get_entries_from_namefile(namefile2, 'OC')
        if ocf2[0][0] is None:
            return True

        hu2, hfpth2, du2, dfpth2 = flopy.modflow.ModflowOc.get_ocoutput_units(
                ocf2[0][0])
        if hu2 != 0:
            entries = get_entries_from_namefile(namefile2, unit=abs(hu2))
            hfpth2, status2 = entries[0][0], entries[0][1]
    else:
        if isinstance(files2, str):
            files2 = [files2]
        for file in files2:
            if 'hds' in os.path.basename(
                    file).lower() or 'hed' in os.path.basename(file).lower():
                hfpth2 = file
                break

    # confirm that there are two files to compare
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
             '{:>15s} {:>15s} {:>15s}\n'.format('STRESS PERIOD', 'TIME STEP',
                                                'HEAD DIFFERENCE') + \
             '{0:>15s} {0:>15s} {0:>15s}\n'.format(15 * '-')

    icnt = 0
    # Process cumulative and incremental
    for idx, time in enumerate(times1):
        h1 = headobj1.get_data(totim=time)
        h2 = headobj2.get_data(totim=time)

        if difftol:
            diffmax, indices = calculate_difftol(h1, h2, htol)
        else:
            diffmax, indices = calculate_diffmax(h1, h2)

        if idx < 1:
            f.write(header)
        f.write('{:15d} {:15d} {:15.6g}\n'.format(kstpkper[idx][1] + 1,
                                                  kstpkper[idx][0] + 1,
                                                  diffmax))

        if diffmax >= htol:
            icnt += 1
            if difftol:
                e = 'Maximum head difference ({}) -- '.format(diffmax) + \
                    '{} tolerance exceeded at '.format(htol) + \
                    '{} node location(s):'.format(indices[0].shape[0])
            else:
                e = 'Maximum head difference ' + \
                    '({}) exceeded '.format(diffmax) + \
                    'at {} node location(s):'.format(indices[0].shape[0])
            e = textwrap.fill(e, width=70, initial_indent='  ',
                              subsequent_indent='  ')
            f.write('{}\n'.format(e))
            e = ''
            for itupe in indices:
                for ind in itupe:
                    e += '{} '.format(ind + 1)  # convert to one-based
            e = textwrap.fill(e, width=70, initial_indent='    ',
                              subsequent_indent='    ')
            f.write('{}\n'.format(e))
            # Write header again, unless it is the last record
            if idx + 1 < len(times1):
                f.write('\n{}'.format(header))

    # Close output file
    if outfile is not None:
        f.close()

    # test for failure
    success = True
    if icnt > 0:
        success = False
    return success


def compare_concs(namefile1, namefile2, precision='single',
                  ctol=0.001, outfile=None, files1=None, files2=None,
                  difftol=False):
    """
    Compare the mt3dms concentration results from these two simulations.

    """
    import numpy as np
    import flopy

    # list of valid extensions
    valid_ext = ['ucn']

    # Get info for first ucn file
    ufpth1 = None
    if files1 is None:
        for ext in valid_ext:
            ucn = get_entries_from_namefile(namefile1, extension=ext)
            ufpth = ucn[0][0]
            if ufpth is not None:
                ufpth1 = ufpth
                break
        if ufpth1 is None:
            ufpth1 = os.path.join(os.path.dirname(namefile1), 'MT3D001.UCN')
    else:
        if isinstance(files1, str):
            files1 = [files1]
        for file in files1:
            for ext in valid_ext:
                if ext in os.path.basename(file).lower():
                    ufpth1 = file
                    break

    # Get info for second ucn file
    ufpth2 = None
    if files2 is None:
        for ext in valid_ext:
            ucn = get_entries_from_namefile(namefile2, extension=ext)
            ufpth = ucn[0][0]
            if ufpth is not None:
                ufpth2 = ufpth
                break
        if ufpth2 is None:
            ufpth2 = os.path.join(os.path.dirname(namefile2), 'MT3D001.UCN')
    else:
        if isinstance(files2, str):
            files2 = [files2]
        for file in files2:
            for ext in valid_ext:
                if ext in os.path.basename(file).lower():
                    ufpth2 = file
                    break

    # confirm that there are two files to compare
    if ufpth1 is None or ufpth2 is None:
        if ufpth1 is None:
            print('  UCN file 1 not set')
        if ufpth2 is None:
            print('  UCN file 2 not set')
        return True

    if not os.path.isfile(ufpth1) or not os.path.isfile(ufpth2):
        if not os.path.isfile(ufpth1):
            print('  {} does not exist'.format(ufpth1))
        if not os.path.isfile(ufpth2):
            print('  {} does not exist'.format(ufpth2))
        return True

    # Open output file
    if outfile is not None:
        f = open(outfile, 'w')
        f.write('Created by pymake.autotest.compare_stages\n')

    # Get stage objects
    uobj1 = flopy.utils.UcnFile(ufpth1, precision=precision)
    uobj2 = flopy.utils.UcnFile(ufpth2, precision=precision)

    # get times
    times1 = uobj1.get_times()
    times2 = uobj2.get_times()
    nt1 = len(times1)
    nt2 = len(times2)
    nt = min(nt1, nt2)

    assert times1[0:nt] == times2[0:nt], 'times in two ucn files are not equal'

    if nt == nt1:
        kstpkper = uobj1.get_kstpkper()
    else:
        kstpkper = uobj2.get_kstpkper()

    header = '{:>15s} {:>15s} {:>15s}\n'.format(' ', ' ', 'MAXIMUM') + \
             '{:>15s} {:>15s} {:>15s}\n'.format('STRESS PERIOD', 'TIME STEP',
                                                'CONC DIFFERENCE') + \
             '{0:>15s} {0:>15s} {0:>15s}\n'.format(15 * '-')

    icnt = 0
    # Process cumulative and incremental
    for idx, time in enumerate(times1[0:nt]):
        try:
            u1 = uobj1.get_data(totim=time)
            u2 = uobj2.get_data(totim=time)

            if difftol:
                diffmax, indices = calculate_difftol(u1, u2, ctol)
            else:
                diffmax, indices = calculate_diffmax(u1, u2)

            if idx < 1:
                f.write(header)
            f.write('{:15d} {:15d} {:15.6g}\n'.format(kstpkper[idx][1] + 1,
                                                      kstpkper[idx][0] + 1,
                                                      diffmax))

            if diffmax >= ctol:
                icnt += 1
                if difftol:
                    e = 'Maximum concentration difference ({})'.format(diffmax) + \
                        ' -- {} tolerance exceeded at '.format(htol) + \
                        '{} node location(s):'.format(indices[0].shape[0])
                else:
                    e = 'Maximum concentration difference ' + \
                        '({}) exceeded '.format(diffmax) + \
                        'at {} node location(s):'.format(indices[0].shape[0])
                e = textwrap.fill(e, width=70, initial_indent='  ',
                                  subsequent_indent='  ')
                f.write('{}\n'.format(e))
                e = ''
                for itupe in indices:
                    for ind in itupe:
                        e += '{} '.format(ind + 1)  # convert to one-based
                e = textwrap.fill(e, width=70, initial_indent='    ',
                                  subsequent_indent='    ')
                f.write('{}\n'.format(e))
                # Write header again, unless it is the last record
                if idx + 1 < len(times1):
                    f.write('\n{}'.format(header))
        except:
            print('  could not process time={}'.format(time))
            print('  terminating ucn processing...')
            break

    # Close output file
    if outfile is not None:
        f.close()

    # test for failure
    success = True
    if icnt > 0:
        success = False
    return success


def compare_stages(namefile1=None, namefile2=None, files1=None, files2=None,
                   htol=0.001, outfile=None, difftol=False):
    """
    Compare the swr stage results from these two simulations.

    """
    import numpy as np
    import flopy

    # list of valid extensions
    valid_ext = ['stg']

    # Get info for first stage file
    sfpth1 = None
    if namefile1 is not None:
        for ext in valid_ext:
            stg = get_entries_from_namefile(namefile1, extension=ext)
            sfpth = stg[0][0]
            if sfpth is not None:
                sfpth1 = sfpth
                break
    elif files1 is not None:
        if isinstance(files1, str):
            files1 = [files1]
        for file in files1:
            for ext in valid_ext:
                if ext in os.path.basename(file).lower():
                    sfpth1 = file
                    break

    # Get info for second stage file
    sfpth2 = None
    if namefile2 is not None:
        for ext in valid_ext:
            stg = get_entries_from_namefile(namefile2, extension=ext)
            sfpth = stg[0][0]
            if sfpth is not None:
                sfpth2 = sfpth
                break
    elif files2 is not None:
        if isinstance(files2, str):
            files2 = [files2]
        for file in files2:
            for ext in valid_ext:
                if ext in os.path.basename(file).lower():
                    sfpth2 = file
                    break

    # confirm that there are two files to compare
    if sfpth1 is None or sfpth2 is None:
        return True

    if not os.path.isfile(sfpth1) or not os.path.isfile(sfpth2):
        return True

    # Open output file
    if outfile is not None:
        f = open(outfile, 'w')
        f.write('Created by pymake.autotest.compare_stages\n')

    # Get stage objects
    sobj1 = flopy.utils.SwrStage(sfpth1)
    sobj2 = flopy.utils.SwrStage(sfpth2)

    # get totim
    times1 =sobj1.get_times()

    # get kswr, kstp, and kper
    kk = sobj1.get_kswrkstpkper()

    header = '{:>15s} {:>15s} {:>15s} {:>15s}\n'.format(' ', ' ', ' ',
                                                        'MAXIMUM') + \
             '{:>15s} {:>15s} {:>15s} {:>15s}\n'.format('STRESS PERIOD',
                                                        'TIME STEP',
                                                        'SWR TIME STEP',
                                                        'STAGE DIFFERENCE') + \
             '{0:>15s} {0:>15s} {0:>15s} {0:>15s}\n'.format(15 * '-')

    icnt = 0
    # Process stage data
    for idx, (kon, time) in enumerate(zip(kk, times1)):
        s1 = sobj1.get_data(totim=time)
        s2 = sobj2.get_data(totim=time)

        if s1 is None or s2 is None:
            continue

        s1 = s1['stage']
        s2 = s2['stage']


        if difftol:
            diffmax, indices = calculate_difftol(s1, s2, htol)
        else:
            diffmax, indices = calculate_diffmax(s1, s2)

        if idx < 1:
            f.write(header)
        f.write('{:15d} {:15d} {:15d} {:15.6g}\n'.format(kon[2] + 1,
                                                         kon[1] + 1,
                                                         kon[0] + 1,
                                                         diffmax))

        if diffmax >= htol:
            icnt += 1
            if difftol:
                e = 'Maximum head difference ({}) -- '.format(diffmax) + \
                    '{} tolerance exceeded at '.format(htol) + \
                    '{} node location(s):'.format(indices[0].shape[0])
            else:
                e = 'Maximum head difference ' + \
                    '({}) exceeded '.format(diffmax) + \
                    'at {} node location(s):'.format(indices[0].shape[0])
            e = textwrap.fill(e, width=70, initial_indent='  ',
                              subsequent_indent='  ')
            f.write('{}\n'.format(e))
            e = ''
            for itupe in indices:
                for ind in itupe:
                    e += '{} '.format(ind + 1)  # convert to one-based
            e = textwrap.fill(e, width=70, initial_indent='    ',
                              subsequent_indent='    ')
            f.write('{}\n'.format(e))
            # Write header again, unless it is the last record
            if idx + 1 < len(times1):
                f.write('\n{}'.format(header))

    # Close output file
    if outfile is not None:
        f.close()

    # test for failure
    success = True
    if icnt > 0:
        success = False
    return success


def calculate_diffmax(v1, v2):
    import numpy as np
    if v1.ndim > 1 or v2.ndim > 1:
        v1 = v1.flatten()
        v2 = v2.flatten()
    if v1.size != v2.size:
        err = 'Error: calculate_difference v1 size ({}) '.format(
                v1.size) + 'is not equal to v2 size ({})'.format(v2.size)
        raise Exception(err)

    diff = abs(v1 - v2)
    diffmax = diff.max()
    indices = np.where(diff == diffmax)
    return diffmax, indices


def calculate_difftol(v1, v2, tol):
    import numpy as np
    if v1.ndim > 1 or v2.ndim > 1:
        v1 = v1.flatten()
        v2 = v2.flatten()
    if v1.size != v2.size:
        err = 'Error: calculate_difference v1 size ({}) '.format(
                v1.size) + 'is not equal to v2 size ({})'.format(v2.size)
        raise Exception(err)

    diff = abs(v1 - v2)
    diffmax = diff.max()
    indices = np.where(diff > tol)
    return diffmax, indices


def compare(namefile1, namefile2, precision='single',
            max_cumpd=0.01, max_incpd=0.01, htol=0.001,
            outfile1=None, outfile2=None,
            files1=None, files2=None):
    """
    Compare the results from two standard simulations
    """

    # Compare budgets from the list files in namefile1 and namefile2
    success1 = compare_budget(namefile1, namefile2,
                              max_cumpd=max_cumpd, max_incpd=max_incpd,
                              outfile=outfile1,
                              files1=files1, files2=files2)
    success2 = compare_heads(namefile1, namefile2, precision=precision,
                             htol=htol, outfile=outfile2,
                             files1=files1, files2=files2)
    success = False
    if success1 and success2:
        success = True
    return success
