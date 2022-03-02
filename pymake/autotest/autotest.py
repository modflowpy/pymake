"""A typical example of using the autotest
functionality for MODFLOW-2005 and comparing the MODFLOW-2005 results to
MODFLOW-2000 results is:

.. code-block:: python

        import pymake

        # Setup
        testpth = "../test/mytest"
        nam1 = "model1.nam"
        pymake.setup(nam1, testpth)

        # run test models
        success, buff = flopy.run_model(
                "mf2005", nam1, model_ws=testpth, silent=True
            )
        if success:
            testpth_reg = os.path.join(testpth, "mf2000")
            nam2 = "model2.name"
            pymake.setup(nam2, testpth_reg)
            success_reg, buff = flopy.run_model(
                    "mf2000", nam2, model_ws=testpth_reg, silent=True
                )

        # compare results
        if success and success_reg:
            fpth = os.path.split(os.path.join(testpth, nam1))[0]
            outfile1 = os.path.join(fpth, "bud.cmp")
            fpth = os.path.split(os.path.join(testpth, nam2))[0]
            outfile2 = os.path.join(fpth, "hds.cmp")
            success_reg = pymake.compare(
                os.path.join(testpth, nam1),
                os.path.join(testpth_reg, nam2),
                max_cumpd=0.01,
                max_incpd=0.01,
                htol=0.001,
                outfile1=outfile1,
                outfile2=outfile2,
            )

        # Clean things up
        if success_reg:
            pymake.teardown(testpth)

Note: autotest functionality will likely be removed from pymake in the future
to a dedicated GitHub repository.

"""
import os
import shutil
import textwrap

import numpy as np

ignore_ext = (
    ".hds",
    ".hed",
    ".bud",
    ".cbb",
    ".cbc",
    ".ddn",
    ".ucn",
    ".glo",
    ".lst",
    ".list",
    ".gwv",
    ".mv",
    ".out",
)


def setup(namefile, dst, remove_existing=True, extrafiles=None):
    """Setup MODFLOW-based model files for autotests.

    Parameters
    ----------
    namefile : str
        MODFLOW-based model name file.
    dst : str
        destination path for comparison model or file(s)
    remove_existing : bool
        boolean indicating if an existing comparision model or file(s) should
        be replaced (default is True)
    extrafiles : str or list of str
        list of extra files to include in the comparision

    Returns
    -------

    """
    # Construct src pth from namefile or lgr file
    src = os.path.dirname(namefile)

    # Create the destination folder, if required
    create_dir = False
    if os.path.exists(dst):
        if remove_existing:
            print("Removing folder " + dst)
            shutil.rmtree(dst)
            create_dir = True
    else:
        create_dir = True
    if create_dir:
        os.mkdir(dst)

    # determine if a namefile is a lgr control file - get individual
    # name files out of the lgr control file
    namefiles = [namefile]
    ext = os.path.splitext(namefile)[1]
    if ".lgr" in ext.lower():
        lines = [line.rstrip("\n") for line in open(namefile)]
        for line in lines:
            if len(line) < 1:
                continue
            if line[0] == "#":
                continue
            t = line.split()
            if ".nam" in t[0].lower():
                fpth = os.path.join(src, t[0])
                namefiles.append(fpth)

    # Make list of files to copy
    files2copy = []
    for fpth in namefiles:
        files2copy.append(os.path.basename(fpth))
        ext = os.path.splitext(fpth)[1]
        # copy additional files contained in the name file and
        # associated package files
        if ext.lower() == ".nam":
            fname = os.path.abspath(fpth)
            files2copy = files2copy + get_input_files(fname)

    if extrafiles is not None:
        if isinstance(extrafiles, str):
            extrafiles = [extrafiles]
        for fl in extrafiles:
            files2copy.append(os.path.basename(fl))

    # Copy the files
    for f in files2copy:
        srcf = os.path.join(src, f)
        dstf = os.path.join(dst, f)

        # Check to see if dstf is going into a subfolder, and create that
        # subfolder if it doesn't exist
        sf = os.path.dirname(dstf)
        if not os.path.isdir(sf):
            os.makedirs(sf)

        # Now copy the file
        if os.path.exists(srcf):
            print("Copy file '" + srcf + "' -> '" + dstf + "'")
            shutil.copy(srcf, dstf)
        else:
            print(srcf + " does not exist")

    return


def setup_comparison(namefile, dst, remove_existing=True):
    """Setup a comparison model or comparision file(s) for a MODFLOW-based
    model.

    Parameters
    ----------
    namefile : str
        MODFLOW-based model name file.
    dst : str
        destination path for comparison model or file(s)
    remove_existing : bool
        boolean indicating if an existing comparision model or file(s) should
        be replaced (default is True)


    Returns
    -------

    """
    # Construct src pth from namefile
    src = os.path.dirname(namefile)
    action = None
    for root, dirs, files in os.walk(src):
        dl = [d.lower() for d in dirs]
        if any(".cmp" in s for s in dl):
            idx = None
            for jdx, d in enumerate(dl):
                if ".cmp" in d:
                    idx = jdx
                    break
            if idx is not None:
                if "mf2005.cmp" in dl[idx] or "mf2005" in dl[idx]:
                    action = dirs[idx]
                elif "mfnwt.cmp" in dl[idx] or "mfnwt" in dl[idx]:
                    action = dirs[idx]
                elif "mfusg.cmp" in dl[idx] or "mfusg" in dl[idx]:
                    action = dirs[idx]
                elif "mf6.cmp" in dl[idx] or "mf6" in dl[idx]:
                    action = dirs[idx]
                elif "libmf6.cmp" in dl[idx] or "libmf6" in dl[idx]:
                    action = dirs[idx]
                else:
                    action = dirs[idx]
                break
    if action is not None:
        dst = os.path.join(dst, f"{action}")
        if not os.path.isdir(dst):
            try:
                os.mkdir(dst)
            except:
                print("Could not make " + dst)
        # clean directory
        else:
            print(f"cleaning...{dst}")
            for root, dirs, files in os.walk(dst):
                for f in files:
                    tpth = os.path.join(root, f)
                    print(f"  removing...{tpth}")
                    os.remove(tpth)
                for d in dirs:
                    tdir = os.path.join(root, d)
                    print(f"  removing...{tdir}")
                    shutil.rmtree(tdir)
        # copy files
        cmppth = os.path.join(src, action)
        files = os.listdir(cmppth)
        files2copy = []
        if action.lower() == ".cmp":
            for file in files:
                if ".cmp" in os.path.splitext(file)[1].lower():
                    files2copy.append(os.path.join(cmppth, file))
            for srcf in files2copy:
                f = os.path.basename(srcf)
                dstf = os.path.join(dst, f)
                # Now copy the file
                if os.path.exists(srcf):
                    print("Copy file '" + srcf + "' -> '" + dstf + "'")
                    shutil.copy(srcf, dstf)
                else:
                    print(srcf + " does not exist")
        else:
            for file in files:
                if ".nam" in os.path.splitext(file)[1].lower():
                    files2copy.append(
                        os.path.join(cmppth, os.path.basename(file))
                    )
                    nf = os.path.join(src, action, os.path.basename(file))
                    setup(nf, dst, remove_existing=remove_existing)
                    break

    return action


def teardown(src):
    """Teardown a autotest directory.

    Parameters
    ----------
    src : str
        autotest directory to teardown

    Returns
    -------

    """
    if os.path.exists(src):
        print("Removing folder " + src)
        shutil.rmtree(src)
    return


def get_input_files(namefile):
    """Return a list of all the input files in this model.

    Parameters
    ----------
    namefile : str
        path to a MODFLOW-based model name file

    Returns
    -------
    filelist : list
        list of MODFLOW-based model input files

    """
    srcdir = os.path.dirname(namefile)
    filelist = []
    fname = os.path.join(srcdir, namefile)
    with open(fname, "r") as f:
        lines = f.readlines()

    for line in lines:
        ll = line.strip().split()
        if len(ll) < 2:
            continue
        if line.strip()[0] in ["#", "!"]:
            continue
        ext = os.path.splitext(ll[2])[1]
        if ext.lower() not in ignore_ext:
            if len(ll) > 3:
                if "replace" in ll[3].lower():
                    continue
            filelist.append(ll[2])

    # Now go through every file and look for other files to copy,
    # such as 'OPEN/CLOSE'.  If found, then add that file to the
    # list of files to copy.
    otherfiles = []
    for fname in filelist:
        fname = os.path.join(srcdir, fname)
        try:
            f = open(fname, "r")
            for line in f:

                # Skip invalid lines
                ll = line.strip().split()
                if len(ll) < 2:
                    continue
                if line.strip()[0] in ["#", "!"]:
                    continue

                if "OPEN/CLOSE" in line.upper():
                    for i, s in enumerate(ll):
                        if "OPEN/CLOSE" in s.upper():
                            stmp = ll[i + 1]
                            stmp = stmp.replace('"', "")
                            stmp = stmp.replace("'", "")
                            otherfiles.append(stmp)
                            break
        except:
            print(fname + " does not exist")

    filelist = filelist + otherfiles

    return filelist


def get_namefiles(pth, exclude=None):
    """Search through a path (pth) for all .nam files.

    Parameters
    ----------
    pth : str
        path to model files
    exclude : str or lst
        File or list of files to exclude from the search (default is None)

    Returns
    -------
    namefiles : lst
        List of namefiles with paths

    """
    namefiles = []
    for root, _, files in os.walk(pth):
        namefiles += [
            os.path.join(root, file) for file in files if file.endswith(".nam")
        ]
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
    """Get entries from a namefile. Can select using FTYPE, UNIT, or file
    extension.

    Parameters
    ----------
    namefile : str
        path to a MODFLOW-based model name file
    ftype : str
        package type
    unit : int
        file unit number
    extension : str
        file extension

    Returns
    -------
    entries : list of tuples
        list of tuples containing FTYPE, UNIT, FNAME, STATUS for each
        namefile entry that meets a user-specified value.

    """
    entries = []
    f = open(namefile, "r")
    for line in f:
        if line.strip() == "":
            continue
        if line[0] == "#":
            continue
        ll = line.strip().split()
        if len(ll) < 3:
            continue
        status = "UNKNOWN"
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
                if ext[0] == ".":
                    ext = ext[1:]
                if extension.lower() == ext.lower():
                    entries.append((filename, ll[0], ll[1], status))
    f.close()
    if len(entries) < 1:
        entries.append((None, None, None, None))
    return entries


def get_sim_name(namefiles, rootpth=None):
    """Get simulation name.

    Parameters
    ----------
    namefiles : str or list of strings
        path(s) to MODFLOW-based model name files
    rootpth : str
        optional root directory path (default is None)

    Returns
    -------
    simname : list
        list of namefiles without the file extension

    """
    if isinstance(namefiles, str):
        namefiles = [namefiles]
    sim_name = []
    for namefile in namefiles:
        t = namefile.split(os.sep)
        if rootpth is None:
            idx = -1
        else:
            idx = t.index(os.path.split(rootpth)[1])

        # build dst with everything after the rootpth and before
        # the namefile file name.
        dst = ""
        if idx < len(t):
            for d in t[idx + 1 : -1]:
                dst += f"{d}_"

        # add namefile basename without extension
        dst += t[-1].replace(".nam", "")
        sim_name.append(dst)

    return sim_name


# modflow 6 readers and copiers
def setup_mf6(
    src, dst, mfnamefile="mfsim.nam", extrafiles=None, remove_existing=True
):
    """Copy all of the MODFLOW 6 input files from the src directory to the dst
    directory.

    Parameters
    ----------
    src : src
        directory path with original MODFLOW 6 input files
    dst : str
        directory path that original MODFLOW 6 input files will be copied to
    mfnamefile : str
        optional MODFLOW 6 simulation name file (default is mfsim.nam)
    extrafiles : bool
        boolean indicating if extra files should be included (default is None)
    remove_existing : bool
        boolean indicating if existing file in dst should be removed (default
        is True)

    Returns
    -------
    mf6inp : list
        list of MODFLOW 6 input files
    mf6outp : list
        list of MODFLOW 6 output files

    """

    # Create the destination folder
    create_dir = False
    if os.path.exists(dst):
        if remove_existing:
            print("Removing folder " + dst)
            shutil.rmtree(dst)
            create_dir = True
    else:
        create_dir = True
    if create_dir:
        os.makedirs(dst)

    # Make list of files to copy
    fname = os.path.join(src, mfnamefile)
    fname = os.path.abspath(fname)
    mf6inp, mf6outp = get_mf6_files(fname)
    files2copy = [mfnamefile] + mf6inp

    # determine if there are any .ex files
    exinp = []
    for f in mf6outp:
        ext = os.path.splitext(f)[1]
        if ext.lower() == ".hds":
            pth = os.path.join(src, f + ".ex")
            if os.path.isfile(pth):
                exinp.append(f + ".ex")
    if len(exinp) > 0:
        files2copy += exinp
    if extrafiles is not None:
        files2copy += extrafiles

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
                print("Could not make " + sf)

        # Now copy the file
        if os.path.exists(srcf):
            print("Copy file '" + srcf + "' -> '" + dstf + "'")
            shutil.copy(srcf, dstf)
        else:
            print(srcf + " does not exist")

    return mf6inp, mf6outp


def get_mf6_comparison(src):
    """Determine comparison type for MODFLOW 6 simulation.

    Parameters
    ----------
    src : str
        directory path to search for comparison types

    Returns
    -------
    action : str
        comparison type

    """
    action = None
    # Possible comparison - the order matters
    optcomp = (
        "compare",
        ".cmp",
        "mf2005",
        "mf2005.cmp",
        "mfnwt",
        "mfnwt.cmp",
        "mfusg",
        "mfusg.cmp",
        "mflgr",
        "mflgr.cmp",
        "libmf6",
        "libmf6.cmp",
        "mf6",
        "mf6.cmp",
    )
    # Construct src pth from namefile
    action = None
    for _, dirs, _ in os.walk(src):
        dl = [d.lower() for d in dirs]
        for oc in optcomp:
            if any(oc in s for s in dl):
                action = oc
                break
    return action


def setup_mf6_comparison(src, dst, remove_existing=True):
    """Setup comparision for MODFLOW 6 simulation.

    Parameters
    ----------
    src : src
        directory path with original MODFLOW 6 input files
    dst : str
        directory path that original MODFLOW 6 input files will be copied to
    remove_existing : bool
        boolean indicating if existing file in dst should be removed (default
        is True)

    Returns
    -------
    action : str
        comparison type

    """
    # get the type of comparison to use (compare, mf2005, etc.)
    action = get_mf6_comparison(src)

    if action is not None:
        dst = os.path.join(dst, f"{action}")
        if not os.path.isdir(dst):
            try:
                os.mkdir(dst)
            except:
                print("Could not make " + dst)
        # clean directory
        else:
            print(f"cleaning...{dst}")
            for root, dirs, files in os.walk(dst):
                for f in files:
                    tpth = os.path.join(root, f)
                    print(f"  removing...{tpth}")
                    os.remove(tpth)
                for d in dirs:
                    tdir = os.path.join(root, d)
                    print(f"  removing...{tdir}")
                    shutil.rmtree(tdir)
        # copy files
        cmppth = os.path.join(src, action)
        files = os.listdir(cmppth)
        files2copy = []
        if action.lower() == "compare" or action.lower() == ".cmp":
            for file in files:
                if ".cmp" in os.path.splitext(file)[1].lower():
                    files2copy.append(os.path.join(cmppth, file))
            for srcf in files2copy:
                f = os.path.basename(srcf)
                dstf = os.path.join(dst, f)
                # Now copy the file
                if os.path.exists(srcf):
                    print("Copy file '" + srcf + "' -> '" + dstf + "'")
                    shutil.copy(srcf, dstf)
                else:
                    print(srcf + " does not exist")
        else:
            if "mf6" in action.lower():
                for file in files:
                    if "mfsim.nam" in file.lower():
                        srcf = os.path.join(cmppth, os.path.basename(file))
                        files2copy.append(srcf)
                        srcdir = os.path.join(src, action)
                        setup_mf6(srcdir, dst, remove_existing=remove_existing)
                        break
            else:
                for file in files:
                    if ".nam" in os.path.splitext(file)[1].lower():
                        srcf = os.path.join(cmppth, os.path.basename(file))
                        files2copy.append(srcf)
                        nf = os.path.join(src, action, os.path.basename(file))
                        setup(nf, dst, remove_existing=remove_existing)
                        break

    return action


def get_mf6_nper(tdisfile):
    """Return the number of stress periods in the MODFLOW 6 model.

    Parameters
    ----------
    tdisfile : str
        path to the TDIS file

    Returns
    -------
    nper : int
        number of stress periods in the simulation

    """
    with open(tdisfile, "r") as f:
        lines = f.readlines()
    line = [line for line in lines if "NPER" in line.upper()][0]
    nper = line.strip().split()[1]
    return nper


def get_mf6_mshape(disfile):
    """Return the shape of the MODFLOW 6 model.

    Parameters
    ----------
    disfile : str
        path to a MODFLOW 6 discretization file

    Returns
    -------
    mshape : tuple
        tuple with the shape of the MODFLOW 6 model.

    """
    with open(disfile, "r") as f:
        lines = f.readlines()

    d = {}
    for line in lines:

        # Skip over blank and commented lines
        ll = line.strip().split()
        if len(ll) < 2:
            continue
        if line.strip()[0] in ["#", "!"]:
            continue

        for key in ["NODES", "NCPL", "NLAY", "NROW", "NCOL"]:
            if ll[0].upper() in key:
                d[key] = int(ll[1])

    if "NODES" in d:
        mshape = (d["NODES"],)
    elif "NCPL" in d:
        mshape = (d["NLAY"], d["NCPL"])
    elif "NLAY" in d:
        mshape = (d["NLAY"], d["NROW"], d["NCOL"])
    else:
        print(d)
        raise Exception("Could not determine model shape")
    return mshape


def get_mf6_files(mfnamefile):
    """Return a list of all the MODFLOW 6 input and output files in this model.

    Parameters
    ----------
    mfnamefile : str
        path to the MODFLOW 6 simulation name file

    Returns
    -------
    filelist : list
        list of MODFLOW 6 input files in a simulation
    outplist : list
        list of MODFLOW 6 output files in a simulation

    """

    srcdir = os.path.dirname(mfnamefile)
    filelist = []
    outplist = []

    filekeys = ["TDIS6", "GWF6", "GWT", "GWF6-GWF6", "GWF-GWT", "IMS6"]
    namefilekeys = ["GWF6", "GWT"]
    namefiles = []

    with open(mfnamefile) as f:

        # Read line and skip comments
        lines = f.readlines()

    for line in lines:

        # Skip over blank and commented lines
        ll = line.strip().split()
        if len(ll) < 2:
            continue
        if line.strip()[0] in ["#", "!"]:
            continue

        for key in filekeys:
            if key in ll[0].upper():
                fname = ll[1]
                filelist.append(fname)

        for key in namefilekeys:
            if key in ll[0].upper():
                fname = ll[1]
                namefiles.append(fname)

    # Go through name files and get files
    for namefile in namefiles:
        fname = os.path.join(srcdir, namefile)
        with open(fname, "r") as f:
            lines = f.readlines()
        insideblock = False

        for line in lines:
            ll = line.upper().strip().split()
            if len(ll) < 2:
                continue
            if ll[0] in "BEGIN" and ll[1] in "PACKAGES":
                insideblock = True
                continue
            if ll[0] in "END" and ll[1] in "PACKAGES":
                insideblock = False

            if insideblock:
                ll = line.strip().split()
                if len(ll) < 2:
                    continue
                if line.strip()[0] in ["#", "!"]:
                    continue
                filelist.append(ll[1])

    # Recursively go through every file and look for other files to copy,
    # such as 'OPEN/CLOSE' and 'TIMESERIESFILE'.  If found, then
    # add that file to the list of files to copy.
    flist = filelist
    # olist = outplist
    while True:
        olist = []
        flist, olist = _get_mf6_external_files(srcdir, olist, flist)
        # add to filelist
        if len(flist) > 0:
            filelist = filelist + flist
        # add to outplist
        if len(olist) > 0:
            outplist = outplist + olist
        # terminate loop if no additional files
        # if len(flist) < 1 and len(olist) < 1:
        if len(flist) < 1:
            break

    return filelist, outplist


def _get_mf6_external_files(srcdir, outplist, files):
    """Get list of external files in a MODFLOW 6 simulation.

    Parameters
    ----------
    srcdir : str
        path to a directory containing a MODFLOW 6 simulation
    outplist : list
        list of output files in a MODFLOW 6 simulation
    files : list
        list of MODFLOW 6 name files

    Returns
    -------

    """
    extfiles = []

    for fname in files:
        fname = os.path.join(srcdir, fname)
        try:
            f = open(fname, "r")
            for line in f:

                # Skip invalid lines
                ll = line.strip().split()
                if len(ll) < 2:
                    continue
                if line.strip()[0] in ["#", "!"]:
                    continue

                if "OPEN/CLOSE" in line.upper():
                    for i, s in enumerate(ll):
                        if s.upper() == "OPEN/CLOSE":
                            stmp = ll[i + 1]
                            stmp = stmp.replace('"', "")
                            stmp = stmp.replace("'", "")
                            extfiles.append(stmp)
                            break

                if "TS6" in line.upper():
                    for i, s in enumerate(ll):
                        if s.upper() == "FILEIN":
                            stmp = ll[i + 1]
                            stmp = stmp.replace('"', "")
                            stmp = stmp.replace("'", "")
                            extfiles.append(stmp)
                            break

                if "TAS6" in line.upper():
                    for i, s in enumerate(ll):
                        if s.upper() == "FILEIN":
                            stmp = ll[i + 1]
                            stmp = stmp.replace('"', "")
                            stmp = stmp.replace("'", "")
                            extfiles.append(stmp)
                            break

                if "OBS6" in line.upper():
                    for i, s in enumerate(ll):
                        if s.upper() == "FILEIN":
                            stmp = ll[i + 1]
                            stmp = stmp.replace('"', "")
                            stmp = stmp.replace("'", "")
                            extfiles.append(stmp)
                            break

                if "EXTERNAL" in line.upper():
                    for i, s in enumerate(ll):
                        if s.upper() == "EXTERNAL":
                            stmp = ll[i + 1]
                            stmp = stmp.replace('"', "")
                            stmp = stmp.replace("'", "")
                            extfiles.append(stmp)
                            break

                if "FILE" in line.upper():
                    for i, s in enumerate(ll):
                        if s.upper() == "FILEIN":
                            stmp = ll[i + 1]
                            stmp = stmp.replace('"', "")
                            stmp = stmp.replace("'", "")
                            extfiles.append(stmp)
                            break

                if "FILE" in line.upper():
                    for i, s in enumerate(ll):
                        if s.upper() == "FILEOUT":
                            stmp = ll[i + 1]
                            stmp = stmp.replace('"', "")
                            stmp = stmp.replace("'", "")
                            outplist.append(stmp)
                            break

        except:
            print("could not get a list of external mf6 files")

    return extfiles, outplist


def get_mf6_ftypes(namefile, ftypekeys):
    """Return a list of FTYPES that are in the name file and in ftypekeys.

    Parameters
    ----------
    namefile : str
        path to a MODFLOW 6 name file
    ftypekeys : list
        list of desired FTYPEs

    Returns
    -------
    ftypes : list
        list of FTYPES that match ftypekeys in namefile

    """
    with open(namefile, "r") as f:
        lines = f.readlines()

    ftypes = []
    for line in lines:

        # Skip over blank and commented lines
        ll = line.strip().split()
        if len(ll) < 2:
            continue
        if line.strip()[0] in ["#", "!"]:
            continue

        for key in ftypekeys:
            if ll[0].upper() in key:
                ftypes.append(ll[0])

    return ftypes


def get_mf6_blockdata(f, blockstr):
    """Return list with all non comments between start and end of block
    specified by blockstr.

    Parameters
    ----------
    f : file object
        open file object
    blockstr : str
        name of block to search

    Returns
    -------
    data : list
        list of data in specified block

    """
    data = []

    # find beginning of block
    for line in f:
        if line[0] != "#":
            t = line.split()
            if t[0].lower() == "begin" and t[1].lower() == blockstr.lower():
                break
    for line in f:
        if line[0] != "#":
            t = line.split()
            if t[0].lower() == "end" and t[1].lower() == blockstr.lower():
                break
            else:
                data.append(line.rstrip())
    return data


# compare functions
def compare_budget(
    namefile1,
    namefile2,
    max_cumpd=0.01,
    max_incpd=0.01,
    outfile=None,
    files1=None,
    files2=None,
):
    """Compare the budget results from two simulations.

    Parameters
    ----------
    namefile1 : str
        namefile path for base model
    namefile2 : str
        namefile path for comparison model
    max_cumpd : float
        maximum percent discrepancy allowed for cumulative budget terms
        (default is 0.01)
    max_incpd : float
        maximum percent discrepancy allowed for incremental budget terms
        (default is 0.01)
    outfile : str
        budget comparison output file name. If outfile is None, no
        comparison output is saved. (default is None)
    files1 : str
        base model output file. If files1 is not None, results
        will be extracted from files1 and namefile1 will not be used.
        (default is None)
    files2 : str
        comparison model output file. If files2 is not None, results
        will be extracted from files2 and namefile2 will not be used.
        (default is None)

    Returns
    -------
    success : bool
        boolean indicating if the difference between budgets are less
        than max_cumpd and max_incpd

    """
    try:
        import flopy
    except:
        msg = "flopy not available - cannot use compare_budget"
        raise ValueError(msg)

    # headers
    headers = ("INCREMENTAL", "CUMULATIVE")
    direction = ("IN", "OUT")

    # Get name of list files
    lst_file1 = None
    if files1 is None:
        lst_file = get_entries_from_namefile(namefile1, "list")
        lst_file1 = lst_file[0][0]
    else:
        if isinstance(files1, str):
            files1 = [files1]
        for file in files1:
            if (
                "list" in os.path.basename(file).lower()
                or "lst" in os.path.basename(file).lower()
            ):
                lst_file1 = file
                break
    lst_file2 = None
    if files2 is None:
        lst_file = get_entries_from_namefile(namefile2, "list")
        lst_file2 = lst_file[0][0]
    else:
        if isinstance(files2, str):
            files2 = [files2]
        for file in files2:
            if (
                "list" in os.path.basename(file).lower()
                or "lst" in os.path.basename(file).lower()
            ):
                lst_file2 = file
                break
    # Determine if there are two files to compare
    if lst_file1 is None or lst_file2 is None:
        print("lst_file1 or lst_file2 is None")
        print(f"lst_file1: {lst_file1}")
        print(f"lst_file2: {lst_file2}")
        return True

    # Open output file
    if outfile is not None:
        f = open(outfile, "w")
        f.write("Created by pymake.autotest.compare\n")

    # Initialize SWR budget objects
    lst1obj = flopy.utils.MfusgListBudget(lst_file1)
    lst2obj = flopy.utils.MfusgListBudget(lst_file2)

    # Determine if there any SWR entries in the budget file
    if not lst1obj.isvalid() or not lst2obj.isvalid():
        return True

    # Get numpy budget tables for lst_file1
    lst1 = []
    lst1.append(lst1obj.get_incremental())
    lst1.append(lst1obj.get_cumulative())

    # Get numpy budget tables for lst_file2
    lst2 = []
    lst2.append(lst2obj.get_incremental())
    lst2.append(lst2obj.get_cumulative())

    icnt = 0
    v0 = np.zeros(2, dtype=float)
    v1 = np.zeros(2, dtype=float)
    err = np.zeros(2, dtype=float)

    # Process cumulative and incremental
    for idx in range(2):
        if idx > 0:
            max_pd = max_cumpd
        else:
            max_pd = max_incpd
        kper = lst1[idx]["stress_period"]
        kstp = lst1[idx]["time_step"]

        # Process each time step
        for jdx in range(kper.shape[0]):

            err[:] = 0.0
            t0 = lst1[idx][jdx]
            t1 = lst2[idx][jdx]

            if outfile is not None:

                maxcolname = 0
                for colname in t0.dtype.names:
                    maxcolname = max(maxcolname, len(colname))

                s = 2 * "\n"
                s += (
                    f"STRESS PERIOD: {kper[jdx] + 1} "
                    + f"TIME STEP: {kstp[jdx] + 1}"
                )
                f.write(s)

                if idx == 0:
                    f.write("\nINCREMENTAL BUDGET\n")
                else:
                    f.write("\nCUMULATIVE BUDGET\n")

                for i, colname in enumerate(t0.dtype.names):
                    if i == 0:
                        s = (
                            f"{'Budget Entry':<21} {'Model 1':>21} "
                            + f"{'Model 2':>21} {'Difference':>21}\n"
                        )
                        f.write(s)
                        s = 87 * "-" + "\n"
                        f.write(s)
                    diff = t0[colname] - t1[colname]
                    s = (
                        f"{colname:<21} {t0[colname]:>21} "
                        + f"{t1[colname]:>21} {diff:>21}\n"
                    )
                    f.write(s)

            v0[0] = t0["TOTAL_IN"]
            v1[0] = t1["TOTAL_IN"]
            if v0[0] > 0.0:
                err[0] = 100.0 * (v1[0] - v0[0]) / v0[0]
            v0[1] = t0["TOTAL_OUT"]
            v1[1] = t1["TOTAL_OUT"]
            if v0[1] > 0.0:
                err[1] = 100.0 * (v1[1] - v0[1]) / v0[1]
            for kdx, t in enumerate(err):
                if abs(t) > max_pd:
                    icnt += 1
                    if outfile is not None:
                        e = (
                            f'"{headers[idx]} {direction[kdx]}" '
                            + f"percent difference ({t})"
                            + f" for stress period {kper[jdx] + 1} "
                            + f"and time step {kstp[jdx] + 1} > {max_pd}."
                            + f" Reference value = {v0[kdx]}. "
                            + f"Simulated value = {v1[kdx]}."
                        )
                        e = textwrap.fill(
                            e,
                            width=70,
                            initial_indent="    ",
                            subsequent_indent="    ",
                        )
                        f.write(f"{e}\n")
                        f.write("\n")

    # Close output file
    if outfile is not None:
        f.close()

    # test for failure
    success = True
    if icnt > 0:
        success = False
    return success


def compare_swrbudget(
    namefile1,
    namefile2,
    max_cumpd=0.01,
    max_incpd=0.01,
    outfile=None,
    files1=None,
    files2=None,
):
    """Compare the SWR budget results from two simulations.

    Parameters
    ----------
    namefile1 : str
        namefile path for base model
    namefile2 : str
        namefile path for comparison model
    max_cumpd : float
        maximum percent discrepancy allowed for cumulative budget terms
        (default is 0.01)
    max_incpd : float
        maximum percent discrepancy allowed for incremental budget terms
        (default is 0.01)
    outfile : str
        budget comparison output file name. If outfile is None, no
        comparison output is saved. (default is None)
    files1 : str
        base model output file. If files1 is not None, results
        will be extracted from files1 and namefile1 will not be used.
        (default is None)
    files2 : str
        comparison model output file. If files2 is not None, results
        will be extracted from files2 and namefile2 will not be used.
        (default is None)

    Returns
    -------
    success : bool
        boolean indicating if the difference between budgets are less
        than max_cumpd and max_incpd

    """
    try:
        import flopy
    except:
        msg = "flopy not available - cannot use compare_swrbudget"
        raise ValueError(msg)

    # headers
    headers = ("INCREMENTAL", "CUMULATIVE")
    direction = ("IN", "OUT")

    # Get name of list files
    list1 = None
    if files1 is None:
        lst = get_entries_from_namefile(namefile1, "list")
        list1 = lst[0][0]
    else:
        for file in files1:
            if (
                "list" in os.path.basename(file).lower()
                or "lst" in os.path.basename(file).lower()
            ):
                list1 = file
                break
    list2 = None
    if files2 is None:
        lst = get_entries_from_namefile(namefile2, "list")
        list2 = lst[0][0]
    else:
        for file in files2:
            if (
                "list" in os.path.basename(file).lower()
                or "lst" in os.path.basename(file).lower()
            ):
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
    v0 = np.zeros(2, dtype=float)
    v1 = np.zeros(2, dtype=float)
    err = np.zeros(2, dtype=float)

    # Open output file
    if outfile is not None:
        f = open(outfile, "w")
        f.write("Created by pymake.autotest.compare\n")

    # Process cumulative and incremental
    for idx in range(2):
        if idx > 0:
            max_pd = max_cumpd
        else:
            max_pd = max_incpd
        kper = lst1[idx]["stress_period"]
        kstp = lst1[idx]["time_step"]

        # Process each time step
        for jdx in range(kper.shape[0]):

            err[:] = 0.0
            t0 = lst1[idx][jdx]
            t1 = lst2[idx][jdx]

            if outfile is not None:

                maxcolname = 0
                for colname in t0.dtype.names:
                    maxcolname = max(maxcolname, len(colname))

                s = 2 * "\n"
                s += (
                    f"STRESS PERIOD: {kper[jdx] + 1} "
                    + f"TIME STEP: {kstp[jdx] + 1}"
                )
                f.write(s)

                if idx == 0:
                    f.write("\nINCREMENTAL BUDGET\n")
                else:
                    f.write("\nCUMULATIVE BUDGET\n")

                for i, colname in enumerate(t0.dtype.names):
                    if i == 0:
                        s = (
                            f"{'Budget Entry':<21} {'Model 1':>21} "
                            + f"{'Model 2':>21} {'Difference':>21}\n"
                        )
                        f.write(s)
                        s = 87 * "-" + "\n"
                        f.write(s)
                    diff = t0[colname] - t1[colname]
                    s = (
                        f"{colname:<21} {t0[colname]:>21} "
                        + f"{t1[colname]:>21} {diff:>21}\n"
                    )
                    f.write(s)

            v0[0] = t0["TOTAL_IN"]
            v1[0] = t1["TOTAL_IN"]
            if v0[0] > 0.0:
                err[0] = 100.0 * (v1[0] - v0[0]) / v0[0]
            v0[1] = t0["TOTAL_OUT"]
            v1[1] = t1["TOTAL_OUT"]
            if v0[1] > 0.0:
                err[1] = 100.0 * (v1[1] - v0[1]) / v0[1]
            for kdx, t in enumerate(err):
                if abs(t) > max_pd:
                    icnt += 1
                    e = (
                        f'"{headers[idx]} {direction[kdx]}" '
                        + f"percent difference ({t})"
                        + f" for stress period {kper[jdx] + 1} "
                        + f"and time step {kstp[jdx] + 1} > {max_pd}."
                        + f" Reference value = {v0[kdx]}. "
                        + f"Simulated value = {v1[kdx]}."
                    )
                    e = textwrap.fill(
                        e,
                        width=70,
                        initial_indent="    ",
                        subsequent_indent="    ",
                    )
                    f.write(f"{e}\n")
                    f.write("\n")

    # Close output file
    if outfile is not None:
        f.close()

    # test for failure
    success = True
    if icnt > 0:
        success = False
    return success


def compare_heads(
    namefile1,
    namefile2,
    precision="auto",
    text="head",
    text2=None,
    htol=0.001,
    outfile=None,
    files1=None,
    files2=None,
    difftol=False,
    verbose=False,
    exfile=None,
    exarr=None,
    maxerr=None,
):
    """Compare the head results from two simulations.

    Parameters
    ----------
    namefile1 : str
        namefile path for base model
    namefile2 : str
        namefile path for comparison model
    precision : str
        precision for binary head file ("auto", "single", or "double")
        default is "auto"
    htol : float
        maximum allowed head difference (default is 0.001)
    outfile : str
        head comparison output file name. If outfile is None, no
        comparison output is saved. (default is None)
    files1 : str
        base model output file. If files1 is not None, results
        will be extracted from files1 and namefile1 will not be used.
        (default is None)
    files2 : str
        comparison model output file. If files2 is not None, results
        will be extracted from files2 and namefile2 will not be used.
        (default is None)
    difftol : bool
        boolean determining if the absolute value of the head
        difference greater than htol should be evaluated (default is False)
    verbose : bool
        boolean indicating if verbose output should be written to the
        terminal (default is False)
    exfile : str
        path to a file with exclusion array data. Head differences will not
        be evaluated where exclusion array values are greater than zero.
        (default is None)
    exarr : numpy.ndarry
        exclusion array. Head differences will not be evaluated where
        exclusion array values are greater than zero. (default is None).
    maxerr : int
        maximum number of head difference greater than htol that should be
        reported. If maxerr is None, all head difference greater than htol
        will be reported. (default is None)

    Returns
    -------
    success : bool
        boolean indicating if the head differences are less than htol.

    """
    try:
        import flopy
    except:
        msg = "flopy not available - cannot use compare_heads"
        raise ValueError(msg)

    if text2 is None:
        text2 = text

    dbs = "DATA(BINARY)"

    # Get head info for namefile1
    hfpth1 = None
    status1 = dbs
    if files1 is None:
        # Get oc info, and return if OC not included in models
        ocf1 = get_entries_from_namefile(namefile1, "OC")
        if ocf1[0][0] is None:
            return True

        hu1, hfpth1, du1, _ = flopy.modflow.ModflowOc.get_ocoutput_units(
            ocf1[0][0]
        )
        if text.lower() == "head":
            iut = hu1
        elif text.lower() == "drawdown":
            iut = du1
        if iut != 0:
            entries = get_entries_from_namefile(namefile1, unit=abs(iut))
            hfpth1, status1 = entries[0][0], entries[0][1]

    else:
        if isinstance(files1, str):
            files1 = [files1]
        for file in files1:
            if text.lower() == "head":
                if (
                    "hds" in os.path.basename(file).lower()
                    or "hed" in os.path.basename(file).lower()
                ):
                    hfpth1 = file
                    break
            elif text.lower() == "drawdown":
                if "ddn" in os.path.basename(file).lower():
                    hfpth1 = file
                    break
            elif text.lower() == "concentration":
                if "ucn" in os.path.basename(file).lower():
                    hfpth1 = file
                    break
            else:
                hfpth1 = file
                break

    # Get head info for namefile2
    hfpth2 = None
    status2 = dbs
    if files2 is None:
        # Get oc info, and return if OC not included in models
        ocf2 = get_entries_from_namefile(namefile2, "OC")
        if ocf2[0][0] is None:
            return True

        hu2, hfpth2, du2, dfpth2 = flopy.modflow.ModflowOc.get_ocoutput_units(
            ocf2[0][0]
        )
        if text.lower() == "head":
            iut = hu2
        elif text.lower() == "drawdown":
            iut = du2
        if iut != 0:
            entries = get_entries_from_namefile(namefile2, unit=abs(iut))
            hfpth2, status2 = entries[0][0], entries[0][1]
    else:
        if isinstance(files2, str):
            files2 = [files2]
        for file in files2:
            if text2.lower() == "head":
                if (
                    "hds" in os.path.basename(file).lower()
                    or "hed" in os.path.basename(file).lower()
                ):
                    hfpth2 = file
                    break
            elif text2.lower() == "drawdown":
                if "ddn" in os.path.basename(file).lower():
                    hfpth2 = file
                    break
            elif text2.lower() == "concentration":
                if "ucn" in os.path.basename(file).lower():
                    hfpth2 = file
                    break
            else:
                hfpth2 = file
                break

    # confirm that there are two files to compare
    if hfpth1 is None or hfpth2 is None:
        print("hfpth1 or hfpth2 is None")
        print(f"hfpth1: {hfpth1}")
        print(f"hfpth2: {hfpth2}")
        return True

    # make sure the file paths exist
    if not os.path.isfile(hfpth1) or not os.path.isfile(hfpth2):
        print("hfpth1 or hfpth2 is not a file")
        print(f"hfpth1 isfile: {os.path.isfile(hfpth1)}")
        print(f"hfpth2 isfile: {os.path.isfile(hfpth2)}")
        return False

    # Open output file
    if outfile is not None:
        f = open(outfile, "w")
        f.write("Created by pymake.autotest.compare\n")
        f.write(f"Performing {text.upper()} to {text2.upper()} comparison\n")

        if exfile is not None:
            f.write(f"Using exclusion file {exfile}\n")
        if exarr is not None:
            f.write("Using exclusion array\n")

        msg = f"{hfpth1} is a "
        if status1 == dbs:
            msg += "binary file."
        else:
            msg += "ascii file."
        f.write(msg + "\n")
        msg = f"{hfpth2} is a "
        if status2 == dbs:
            msg += "binary file."
        else:
            msg += "ascii file."
        f.write(msg + "\n")

    # Process exclusion data
    exd = None
    # get data from exclusion file
    if exfile is not None:
        e = None
        if isinstance(exfile, str):
            try:
                exd = np.genfromtxt(exfile).flatten()
            except:
                e = (
                    "Could not read exclusion "
                    + f"file {os.path.basename(exfile)}"
                )
                print(e)
                return False
        else:
            e = "exfile is not a valid file path"
            print(e)
            return False

    # process exclusion array
    if exarr is not None:
        e = None
        if isinstance(exarr, np.ndarray):
            if exd is None:
                exd = exarr.flatten()
            else:
                exd += exarr.flatten()
        else:
            e = "exarr is not a numpy array"
            print(e)
            return False

    # Get head objects
    status1 = status1.upper()
    unstructured1 = False
    if status1 == dbs:
        headobj1 = flopy.utils.HeadFile(
            hfpth1, precision=precision, verbose=verbose, text=text
        )
        txt = headobj1.recordarray["text"][0]
        if isinstance(txt, bytes):
            txt = txt.decode("utf-8")
        if "HEADU" in txt:
            unstructured1 = True
            headobj1 = flopy.utils.HeadUFile(
                hfpth1, precision=precision, verbose=verbose
            )
    else:
        headobj1 = flopy.utils.FormattedHeadFile(
            hfpth1, verbose=verbose, text=text
        )

    status2 = status2.upper()
    unstructured2 = False
    if status2 == dbs:
        headobj2 = flopy.utils.HeadFile(
            hfpth2, precision=precision, verbose=verbose, text=text2
        )
        txt = headobj2.recordarray["text"][0]
        if isinstance(txt, bytes):
            txt = txt.decode("utf-8")
        if "HEADU" in txt:
            unstructured2 = True
            headobj2 = flopy.utils.HeadUFile(
                hfpth2, precision=precision, verbose=verbose
            )
    else:
        headobj2 = flopy.utils.FormattedHeadFile(
            hfpth2, verbose=verbose, text=text2
        )

    # get times
    times1 = headobj1.get_times()
    times2 = headobj2.get_times()
    for (t1, t2) in zip(times1, times2):
        if not np.allclose([t1], [t2]):
            msg = "times in two head files are not " + f"equal ({t1},{t2})"
            raise ValueError(msg)

    kstpkper = headobj1.get_kstpkper()

    line_separator = 15 * "-"
    header = (
        f"{' ':>15s} {' ':>15s} {'MAXIMUM':>15s} {'EXCEEDS':>15s}\n"
        + f"{'STRESS PERIOD':>15s} {'TIME STEP':>15s} "
        + f"{'HEAD DIFFERENCE':>15s} {'CRITERIA':>15s}\n"
        + f"{line_separator:>15s} {line_separator:>15s} "
        + f"{line_separator:>15s} {line_separator:>15s}\n"
    )

    if verbose:
        print(f"Comparing results for {len(times1)} times")

    icnt = 0
    # Process cumulative and incremental
    for idx, (t1, t2) in enumerate(zip(times1, times2)):
        h1 = headobj1.get_data(totim=t1)
        if unstructured1:
            temp = np.array([])
            for a in h1:
                temp = np.hstack((temp, a))
            h1 = temp
        h2 = headobj2.get_data(totim=t2)
        if unstructured2:
            temp = np.array([])
            for a in h2:
                temp = np.hstack((temp, a))
            h2 = temp

        if exd is not None:
            # reshape exd to the shape of the head arrays
            if idx == 0:
                e = (
                    f"shape of exclusion data ({exd.shape})"
                    + "can not be reshaped to the size of the "
                    + f"head arrays ({h1.shape})"
                )
                if h1.flatten().shape != exd.shape:
                    raise ValueError(e)
                exd = exd.reshape(h1.shape)
                iexd = exd > 0

            # reset h1 and h2 to the same value in the excluded area
            h1[iexd] = 0.0
            h2[iexd] = 0.0

        if difftol:
            diffmax, indices = _calculate_difftol(h1, h2, htol)
        else:
            diffmax, indices = _calculate_diffmax(h1, h2)

        if outfile is not None:
            if idx < 1:
                f.write(header)
            if diffmax > htol:
                sexceed = "*"
            else:
                sexceed = ""
            kk1 = kstpkper[idx][1] + 1
            kk0 = kstpkper[idx][0] + 1
            f.write(f"{kk1:15d} {kk0:15d} {diffmax:15.6g} {sexceed:15s}\n")

        if diffmax >= htol:
            icnt += 1
            if outfile is not None:
                if difftol:
                    ee = (
                        "Maximum absolute head difference "
                        + f"({diffmax}) -- "
                        + f"{htol} tolerance exceeded at "
                        + f"{indices[0].shape[0]} node location(s)"
                    )
                else:
                    ee = (
                        "Maximum absolute head difference "
                        + f"({diffmax}) exceeded "
                        + f"at {indices[0].shape[0]} node location(s)"
                    )
                e = textwrap.fill(
                    ee + ":",
                    width=70,
                    initial_indent="  ",
                    subsequent_indent="  ",
                )

                if verbose:
                    f.write(f"{ee}\n")
                    print(ee + f" at time {t1}")

                e = ""
                ncells = h1.flatten().shape[0]
                fmtn = "{:" + f"{len(str(ncells))}" + "d}"
                for itupe in indices:
                    for jdx, ind in enumerate(itupe):
                        iv = np.unravel_index(ind, h1.shape)
                        iv = tuple(i + 1 for i in iv)
                        v1 = h1.flatten()[ind]
                        v2 = h2.flatten()[ind]
                        d12 = v1 - v2
                        # e += '    ' + fmtn.format(jdx + 1) + ' node: '
                        # e += fmtn.format(ind + 1)  # convert to one-based
                        e += "    " + fmtn.format(jdx + 1)
                        e += f" {iv}"
                        e += " -- "
                        e += f"h1: {v1:20} "
                        e += f"h2: {v2:20} "
                        e += f"diff: {d12:20}\n"
                        if isinstance(maxerr, int):
                            if jdx + 1 >= maxerr:
                                break
                    if verbose:
                        f.write(f"{e}\n")
                # Write header again, unless it is the last record
                if verbose:
                    if idx + 1 < len(times1):
                        f.write(f"\n{header}")

    # Close output file
    if outfile is not None:
        f.close()

    # test for failure
    success = True
    if icnt > 0:
        success = False
    return success


def compare_concs(
    namefile1,
    namefile2,
    precision="auto",
    ctol=0.001,
    outfile=None,
    files1=None,
    files2=None,
    difftol=False,
    verbose=False,
):
    """Compare the mt3dms and mt3dusgs concentration results from two
    simulations.

    Parameters
    ----------
    namefile1 : str
        namefile path for base model
    namefile2 : str
        namefile path for comparison model
    precision : str
        precision for binary head file ("auto", "single", or "double")
        default is "auto"
    ctol : float
        maximum allowed concentration difference (default is 0.001)
    outfile : str
        concentration comparison output file name. If outfile is None, no
        comparison output is saved. (default is None)
    files1 : str
        base model output file. If files1 is not None, results
        will be extracted from files1 and namefile1 will not be used.
        (default is None)
    files2 : str
        comparison model output file. If files2 is not None, results
        will be extracted from files2 and namefile2 will not be used.
        (default is None)
    difftol : bool
        boolean determining if the absolute value of the concentration
        difference greater than ctol should be evaluated (default is False)
    verbose : bool
        boolean indicating if verbose output should be written to the
        terminal (default is False)

    Returns
    -------
    success : bool
        boolean indicating if the concentration differences are less than
        ctol.

    Returns
    -------

    """
    try:
        import flopy
    except:
        msg = "flopy not available - cannot use compare_concs"
        raise ValueError(msg)

    # list of valid extensions
    valid_ext = ["ucn"]

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
            ufpth1 = os.path.join(os.path.dirname(namefile1), "MT3D001.UCN")
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
            ufpth2 = os.path.join(os.path.dirname(namefile2), "MT3D001.UCN")
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
            print("  UCN file 1 not set")
        if ufpth2 is None:
            print("  UCN file 2 not set")
        return True

    if not os.path.isfile(ufpth1) or not os.path.isfile(ufpth2):
        if not os.path.isfile(ufpth1):
            print(f"  {ufpth1} does not exist")
        if not os.path.isfile(ufpth2):
            print(f"  {ufpth2} does not exist")
        return True

    # Open output file
    if outfile is not None:
        f = open(outfile, "w")
        f.write("Created by pymake.autotest.compare_concs\n")

    # Get stage objects
    uobj1 = flopy.utils.UcnFile(ufpth1, precision=precision, verbose=verbose)
    uobj2 = flopy.utils.UcnFile(ufpth2, precision=precision, verbose=verbose)

    # get times
    times1 = uobj1.get_times()
    times2 = uobj2.get_times()
    nt1 = len(times1)
    nt2 = len(times2)
    nt = min(nt1, nt2)

    for (t1, t2) in zip(times1, times2):
        if not np.allclose([t1], [t2]):
            msg = f"times in two ucn files are not equal ({t1},{t2})"
            raise ValueError(msg)

    if nt == nt1:
        kstpkper = uobj1.get_kstpkper()
    else:
        kstpkper = uobj2.get_kstpkper()

    line_separator = 15 * "-"
    header = (
        f"{' ':>15s} {' ':>15s} {'MAXIMUM':>15s}\n"
        + f"{'STRESS PERIOD':>15s} {'TIME STEP':>15s} "
        + f"{'CONC DIFFERENCE':>15s}\n"
        + f"{line_separator:>15s} "
        + f"{line_separator:>15s} "
        + f"{line_separator:>15s}\n"
    )

    if verbose:
        print(f"Comparing results for {len(times1)} times")

    icnt = 0
    # Process cumulative and incremental
    for idx, time in enumerate(times1[0:nt]):
        try:
            u1 = uobj1.get_data(totim=time)
            u2 = uobj2.get_data(totim=time)

            if difftol:
                diffmax, indices = _calculate_difftol(u1, u2, ctol)
            else:
                diffmax, indices = _calculate_diffmax(u1, u2)

            if outfile is not None:
                if idx < 1:
                    f.write(header)
                f.write(
                    f"{kstpkper[idx][1] + 1:15d} "
                    + f"{kstpkper[idx][0] + 1:15d} "
                    + f"{diffmax:15.6g}\n"
                )

            if diffmax >= ctol:
                icnt += 1
                if outfile is not None:
                    if difftol:
                        ee = (
                            f"Maximum concentration difference ({diffmax})"
                            + f" -- {ctol} tolerance exceeded at "
                            + f"{indices[0].shape[0]} node location(s)"
                        )
                    else:
                        ee = (
                            "Maximum concentration difference "
                            + f"({diffmax}) exceeded "
                            + f"at {indices[0].shape[0]} node location(s)"
                        )
                    e = textwrap.fill(
                        ee + ":",
                        width=70,
                        initial_indent="  ",
                        subsequent_indent="  ",
                    )
                    f.write(f"{e}\n")
                    if verbose:
                        print(ee + f" at time {time}")
                    e = ""
                    for itupe in indices:
                        for ind in itupe:
                            e += f"{ind + 1} "  # convert to one-based
                    e = textwrap.fill(
                        e,
                        width=70,
                        initial_indent="    ",
                        subsequent_indent="    ",
                    )
                    f.write(f"{e}\n")
                    # Write header again, unless it is the last record
                    if idx + 1 < len(times1):
                        f.write(f"\n{header}")
        except:
            print(f"  could not process time={time}")
            print("  terminating ucn processing...")
            break

    # Close output file
    if outfile is not None:
        f.close()

    # test for failure
    success = True
    if icnt > 0:
        success = False
    return success


def compare_stages(
    namefile1=None,
    namefile2=None,
    files1=None,
    files2=None,
    htol=0.001,
    outfile=None,
    difftol=False,
    verbose=False,
):
    """Compare SWR process stage results from two simulations.

    Parameters
    ----------
    namefile1 : str
        namefile path for base model
    namefile2 : str
        namefile path for comparison model
    precision : str
        precision for binary head file ("auto", "single", or "double")
        default is "auto"
    htol : float
        maximum allowed stage difference (default is 0.001)
    outfile : str
        head comparison output file name. If outfile is None, no
        comparison output is saved. (default is None)
    files1 : str
        base model output file. If files1 is not None, results
        will be extracted from files1 and namefile1 will not be used.
        (default is None)
    files2 : str
        comparison model output file. If files2 is not None, results
        will be extracted from files2 and namefile2 will not be used.
        (default is None)
    difftol : bool
        boolean determining if the absolute value of the stage
        difference greater than htol should be evaluated (default is False)
    verbose : bool
        boolean indicating if verbose output should be written to the
        terminal (default is False)

    Returns
    -------
    success : bool
        boolean indicating if the stage differences are less than htol.

    """
    try:
        import flopy
    except:
        msg = "flopy not available - cannot use compare_stages"
        raise ValueError(msg)

    # list of valid extensions
    valid_ext = ["stg"]

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
        print("spth1 or spth2 is None")
        print(f"spth1: {sfpth1}")
        print(f"spth2: {sfpth2}")
        return False

    if not os.path.isfile(sfpth1) or not os.path.isfile(sfpth2):
        print("spth1 or spth2 is not a file")
        print(f"spth1 isfile: {os.path.isfile(sfpth1)}")
        print(f"spth2 isfile: {os.path.isfile(sfpth2)}")
        return False

    # Open output file
    if outfile is not None:
        f = open(outfile, "w")
        f.write("Created by pymake.autotest.compare_stages\n")

    # Get stage objects
    sobj1 = flopy.utils.SwrStage(sfpth1, verbose=verbose)
    sobj2 = flopy.utils.SwrStage(sfpth2, verbose=verbose)

    # get totim
    times1 = sobj1.get_times()

    # get kswr, kstp, and kper
    kk = sobj1.get_kswrkstpkper()

    line_separator = 15 * "-"
    header = (
        f"{' ':>15s} {' ':>15s} {' ':>15s} {'MAXIMUM':>15s}\n"
        + f"{'STRESS PERIOD':>15s} "
        + f"{'TIME STEP':>15s} "
        + f"{'SWR TIME STEP':>15s} "
        + f"{'STAGE DIFFERENCE':>15s}\n"
        + f"{line_separator:>15s} "
        + f"{line_separator:>15s} "
        + f"{line_separator:>15s} "
        + f"{line_separator:>15s}\n"
    )

    if verbose:
        print(f"Comparing results for {len(times1)} times")

    icnt = 0
    # Process stage data
    for idx, (kon, time) in enumerate(zip(kk, times1)):
        s1 = sobj1.get_data(totim=time)
        s2 = sobj2.get_data(totim=time)

        if s1 is None or s2 is None:
            continue

        s1 = s1["stage"]
        s2 = s2["stage"]

        if difftol:
            diffmax, indices = _calculate_difftol(s1, s2, htol)
        else:
            diffmax, indices = _calculate_diffmax(s1, s2)

        if outfile is not None:
            if idx < 1:
                f.write(header)
            f.write(
                f"{kon[2] + 1:15d} "
                + f"{kon[1] + 1:15d} "
                + f"{kon[0] + 1:15d} "
                + f"{diffmax:15.6g}\n"
            )

        if diffmax >= htol:
            icnt += 1
            if outfile is not None:
                if difftol:
                    ee = (
                        f"Maximum head difference ({diffmax}) -- "
                        + f"{htol} tolerance exceeded at "
                        + f"{indices[0].shape[0]} node location(s)"
                    )
                else:
                    ee = (
                        "Maximum head difference "
                        + f"({diffmax}) exceeded "
                        + f"at {indices[0].shape[0]} node location(s):"
                    )
                e = textwrap.fill(
                    ee + ":",
                    width=70,
                    initial_indent="  ",
                    subsequent_indent="  ",
                )
                f.write(f"{e}\n")
                if verbose:
                    print(ee + f" at time {time}")
                e = ""
                for itupe in indices:
                    for ind in itupe:
                        e += f"{ind + 1} "  # convert to one-based
                e = textwrap.fill(
                    e,
                    width=70,
                    initial_indent="    ",
                    subsequent_indent="    ",
                )
                f.write(f"{e}\n")
                # Write header again, unless it is the last record
                if idx + 1 < len(times1):
                    f.write(f"\n{header}")

    # Close output file
    if outfile is not None:
        f.close()

    # test for failure
    success = True
    if icnt > 0:
        success = False
    return success


def _calculate_diffmax(v1, v2):
    """Calculate the maximum difference between two vectors.

    Parameters
    ----------
    v1 : numpy.ndarray
        array of base model results
    v2 : numpy.ndarray
        array of comparison model results

    Returns
    -------
    diffmax : float
        absolute value of the maximum difference in v1 and v2 array values
    indices : numpy.ndarry
        indices where the absolute value of the difference is equal to the
        absolute value of the maximum difference.

    """
    if v1.ndim > 1 or v2.ndim > 1:
        v1 = v1.flatten()
        v2 = v2.flatten()
    if v1.size != v2.size:
        err = (
            f"Error: calculate_difference v1 size ({v1.size}) "
            + f"is not equal to v2 size ({v2.size})"
        )
        raise Exception(err)

    diff = abs(v1 - v2)
    diffmax = diff.max()
    return diffmax, np.where(diff == diffmax)


def _calculate_difftol(v1, v2, tol):
    """Calculate the difference between two arrays relative to a tolerance.

    Parameters
    ----------
    v1 : numpy.ndarray
        array of base model results
    v2 : numpy.ndarray
        array of comparison model results
    tol : float
        tolerance used to evaluate base and comparison models

    Returns
    -------
    diffmax : float
        absolute value of the maximum difference in v1 and v2 array values
    indices : numpy.ndarry
        indices where the absolute value of the difference exceed the
        specified tolerance.

    """
    if v1.ndim > 1 or v2.ndim > 1:
        v1 = v1.flatten()
        v2 = v2.flatten()
    if v1.size != v2.size:
        err = (
            f"Error: calculate_difference v1 size ({v1.size}) "
            + f"is not equal to v2 size ({v2.size})"
        )
        raise Exception(err)

    diff = abs(v1 - v2)
    return diff.max(), np.where(diff > tol)


def compare(
    namefile1,
    namefile2,
    precision="auto",
    max_cumpd=0.01,
    max_incpd=0.01,
    htol=0.001,
    outfile1=None,
    outfile2=None,
    files1=None,
    files2=None,
):
    """Compare the budget and head results for two MODFLOW-based model
    simulations.

    Parameters
    ----------
    namefile1 : str
        namefile path for base model
    namefile2 : str
        namefile path for comparison model
    precision : str
        precision for binary head file ("auto", "single", or "double")
        default is "auto"
    max_cumpd : float
        maximum percent discrepancy allowed for cumulative budget terms
        (default is 0.01)
    max_incpd : float
        maximum percent discrepancy allowed for incremental budget terms
        (default is 0.01)
    htol : float
        maximum allowed head difference (default is 0.001)
    outfile1 : str
        budget comparison output file name. If outfile1 is None, no budget
        comparison output is saved. (default is None)
    outfile2 : str
        head comparison output file name. If outfile2 is None, no head
        comparison output is saved. (default is None)
    files1 : str
        base model output file. If files1 is not None, results
        will be extracted from files1 and namefile1 will not be used.
        (default is None)
    files2 : str
        comparison model output file. If files2 is not None, results
        will be extracted from files2 and namefile2 will not be used.
        (default is None)

    Returns
    -------
    success : bool
        boolean indicating if the budget and head differences are less than
        max_cumpd, max_incpd, and htol.

    """

    # Compare budgets from the list files in namefile1 and namefile2
    success1 = compare_budget(
        namefile1,
        namefile2,
        max_cumpd=max_cumpd,
        max_incpd=max_incpd,
        outfile=outfile1,
        files1=files1,
        files2=files2,
    )
    success2 = compare_heads(
        namefile1,
        namefile2,
        precision=precision,
        htol=htol,
        outfile=outfile2,
        files1=files1,
        files2=files2,
    )
    success = False
    if success1 and success2:
        success = True
    return success
