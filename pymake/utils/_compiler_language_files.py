"""Private functions for processing c/c++ and fortran files"""

import os

from ._dag import _order_c_source_files, _order_f_source_files


def _get_fortran_files(srcfiles, extensions=False):
    """Return a list of fortran files or unique fortran file extensions.

    Parameters
    ----------
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
    if isinstance(srcfiles, (str,)):
        srcfiles = [srcfiles]
    files_out = []
    for srcfile in srcfiles:
        ext = os.path.splitext(srcfile)[1]
        if ext.lower() in (
            ".f",
            ".for",
            ".f90",
            ".fpp",
        ):
            if extensions:
                # save unique extension
                if ext not in files_out:
                    files_out.append(ext)
            else:
                files_out.append(srcfile)
    if len(files_out) < 1:
        files_out = None
    return files_out


def _get_c_files(srcfiles, extensions=False):
    """Return a list of c and cpp files or unique c and cpp file extensions.

    Parameters
    ----------
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
        if ext.lower() in (
            ".c",
            ".cpp",
        ):
            if extensions:
                if ext not in files_out:
                    files_out.append(ext)
            else:
                files_out.append(srcfile)
    if len(files_out) < 1:
        files_out = None
    return files_out


def _get_iso_c(srcfiles):
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
            msg = "get_iso_c: could not " + f"open {os.path.basename(srcfile)}"
            raise FileNotFoundError(msg)

    return iso_c


def _preprocess_file(srcfiles, meson=False):
    """Determine if the file should be preprocessed.

    Parameters
    ----------
    srcfiles : str or list
        source file path or list of source file paths
    meson : bool
        boolean indicating if the preprocess should be set to False
        if all files with preprocessing directives have a *.F or *.F90
        file extension. (default is False)

    Returns
    -------
    preprocess : bool
        flag indicating if the file should be preprocessed

    """
    if isinstance(srcfiles, str):
        srcfiles = [srcfiles]

    preprocess = False
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
                if linelist[0].lower() in (
                    "#define",
                    "#undef",
                    "#ifdef",
                    "#ifndef",
                    "#if",
                    "#error",
                ):
                    if meson:
                        file_extension = os.path.splitext(srcfile)[1]
                        if file_extension not in (
                            ".F",
                            ".F90",
                        ):
                            preprocess = True
                    else:
                        preprocess = True
                    break

            # terminate file content search if preprocess is True
            if preprocess:
                break

        else:
            msg = "_preprocess_file: could not " + f"open {os.path.basename(srcfile)}"
            raise FileNotFoundError(msg)

    return preprocess


def _get_main(srcfiles):
    """Determine if the file should be preprocessed.

    Parameters
    ----------
    srcfiles : str or list
        source file path or list of source file paths

    Returns
    -------
    preprocess : bool
        flag indicating if the file should be preprocessed

    """
    if isinstance(srcfiles, str):
        srcfiles = [srcfiles]

    main_file = None
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
                linetrim = line.strip().lower()
                if len(linetrim) == 0:
                    continue
                for comment in (
                    "!",
                    "c",
                    "/*",
                    "*/",
                    "//",
                ):
                    if linetrim.startswith(comment):
                        continue
                for main in (
                    "int main(",
                    "program ",
                ):
                    if linetrim.startswith(main):
                        main_file = srcfile
                        break

            # terminate file content search if preprocess is True
            if main_file is not None:
                break

        else:
            msg = "_get_main: could not " + f"open {os.path.basename(srcfile)}"
            raise FileNotFoundError(msg)

    return main_file


def _get_srcfiles(srcdir, include_subdir):
    """Get a list of source files in source file directory srcdir

    Parameters
    ----------
    srcdir : str
        path for directory containing source files
    include_subdirs : bool
        boolean indicating source files in srcdir subdirectories should be
        included in the build

    Returns
    -------
    srcfiles : list
        list of fortran and c/c++ file in srcdir

    """
    # create a list of all c(pp), f and f90 source files
    templist = []
    for path, _, files in os.walk(srcdir):
        for file in files:
            if not include_subdir:
                if path != srcdir:
                    continue
            file = os.path.join(os.path.join(path, file))
            templist.append(file)
    srcfiles = []
    for file in templist:
        if (
            file.lower().endswith(".f")
            or file.lower().endswith(".f90")
            or file.lower().endswith(".for")
            or file.lower().endswith(".fpp")
            or file.lower().endswith(".c")
            or file.lower().endswith(".cpp")
        ):
            srcfiles.append(os.path.relpath(file, os.getcwd()))
    return sorted(srcfiles)


def _get_ordered_srcfiles(all_srcfiles, networkx):
    """Create a list of ordered source files (both fortran and c). Ordering is
    build using a directed acyclic graph to determine module dependencies.

    Parameters
    ----------
    all_srcfiles : list
        list of all fortran and c/c++ source files
    networkx : bool
        boolean indicating if the NetworkX python package should be used
        to determine the DAG.

    Returns
    -------
    ordered_srcfiles : list
        list of ordered source files

    """
    cfiles = []
    ffiles = []
    for file in all_srcfiles:
        if (
            file.lower().endswith(".f")
            or file.lower().endswith(".f90")
            or file.lower().endswith(".for")
            or file.lower().endswith(".fpp")
        ):
            ffiles.append(file)
        elif file.lower().endswith(".c") or file.lower().endswith(".cpp"):
            cfiles.append(file)

    # order the source files using the directed acyclic graph in _dag.py
    ordered_srcfiles = []
    if ffiles:
        ordered_srcfiles += _order_f_source_files(ffiles, networkx)

    if cfiles:
        ordered_srcfiles += _order_c_source_files(cfiles, networkx)

    return ordered_srcfiles
