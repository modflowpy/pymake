import os

from .dag import order_source_files, order_c_source_files


def get_fortran_files(srcfiles, extensions=False):
    """Return a list of fortran files or unique fortran file extensions.

    Parameters
    -------
    srcfiles : list
        list of source file names
    extensions : bool
        flag controls return of either a list of fortran files or
        a list of unique fortran file extensions

    Returns
    -------
    files_out : list
        list of fortran files or unique fortran file extensions

    """
    files_out = []
    for srcfile in srcfiles:
        ext = os.path.splitext(srcfile)[1]
        if ext.lower() in [".f", ".for", ".f90", ".fpp"]:
            if extensions:
                # save unique extension
                if ext not in files_out:
                    files_out.append(ext)
            else:
                files_out.append(srcfile)
    if len(files_out) < 1:
        files_out = None
    return files_out


def get_c_files(srcfiles, extensions=False):
    """Return a list of c and cpp files or unique c and cpp file extensions.

    Parameters
    -------
    srcfiles : list
        list of source file names
    extensions : bool
        flag controls return of either a list of c and cpp files or
        a list of unique c and cpp file extensions

    Returns
    -------
    files_out : list
        list of c or cpp files or uniques c and cpp file extensions

    """
    files_out = []
    for srcfile in srcfiles:
        ext = os.path.splitext(srcfile)[1]
        if ext.lower() in [".c", ".cpp"]:
            if extensions:
                if ext not in files_out:
                    files_out.append(ext)
            else:
                files_out.append(srcfile)
    if len(files_out) < 1:
        files_out = None
    return files_out


def get_iso_c(srcfiles):
    """Determine if iso_c_binding is used so that the correct c/c++ compiler
    flags can be set. All fortran files are scanned.

    Parameters
    ----------
    srcfiles : list
        list of fortran source files

    Returns
    -------
    iso_c : bool
        flag indicating if iso_c_binding is used in any fortran file

    """
    iso_c = False
    for srcfile in srcfiles:
        if os.path.exists(srcfile):
            # open the file
            f = open(srcfile, "rb")

            # read the file
            lines = f.read()

            # decode the file
            lines = lines.decode("ascii", "replace").splitlines()

            # develop a list of modules in the file
            for line in lines:
                linelist = line.strip().split()
                if len(linelist) == 0:
                    continue
                if linelist[0].upper() == "USE":
                    modulename = linelist[1].split(",")[0].upper()
                    if "ISO_C_BINDING" == modulename:
                        iso_c = True
                        break

            # terminate file content search if iso_c is True
            if iso_c:
                break
        else:
            msg = "get_iso_c: could not " + "open {}".format(
                os.path.basename(srcfile)
            )
            raise FileNotFoundError(msg)

    return iso_c


def get_ordered_srcfiles(srcdir, include_subdir=False):
    """Create a list of ordered source files (both fortran and c). Ordering is
    build using a directed acyclic graph to determine module dependencies.

    Parameters
    ----------
    srcdir : str
        path for directory containing source files
    include_subdir : bool
        flag indicating if source files are in subdirectories in srcdir

    Returns
    -------
    orderedsourcefiles : list
        list of ordered source files

    """
    # create a list of all c(pp), f and f90 source files
    templist = []
    for path, _, files in os.walk(srcdir):
        for name in files:
            if not include_subdir:
                if path != srcdir:
                    continue
            f = os.path.join(os.path.join(path, name))
            templist.append(f)
    cfiles = []  # mja
    srcfiles = []
    for f in templist:
        if (
            f.lower().endswith(".f")
            or f.lower().endswith(".f90")
            or f.lower().endswith(".for")
            or f.lower().endswith(".fpp")
        ):
            srcfiles.append(f)
        elif f.lower().endswith(".c") or f.lower().endswith(".cpp"):  # mja
            cfiles.append(f)  # mja

    srcfileswithpath = []
    for srcfile in srcfiles:
        # s = os.path.join(srcdir, srcfile)
        s = srcfile
        srcfileswithpath.append(s)

    # from mja
    cfileswithpath = []
    for srcfile in cfiles:
        # s = os.path.join(srcdir, srcfile)
        s = srcfile
        cfileswithpath.append(s)

    # order the source files using the directed acyclic graph in dag.py
    orderedsourcefiles = []
    if len(srcfileswithpath) > 0:
        orderedsourcefiles += order_source_files(srcfileswithpath)

    if len(cfileswithpath) > 0:
        orderedsourcefiles += order_c_source_files(cfileswithpath)

    return orderedsourcefiles
