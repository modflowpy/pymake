import os
import sys
import shutil
import types

from .usgsprograms import usgs_program_data


def get_function_names(module, select_name=None):
    """Get a dictionary of functions available in a user-specified source file.
    This function was developed to create a dictionary of functions in this
    source file (build_apps.py). Optionally, the user can get a get a
    dictionary of functions that contain a specific text string in the name.

    Parameters
    ----------
    module : module
        module to evaluate function names
    select_name : str
        string that is used to select a subset of the available functions in
        the module

    Returns
    -------
    func : dict
        dictionary with function name keys and values set to function pointers

    """
    func = {}
    for key, value in module.__dict__.items():
        ladd = False
        if isinstance(value, types.FunctionType):
            if select_name is None:
                ladd = True
            else:
                if select_name in value.__name__:
                    ladd = True
            if ladd:
                func[value.__name__] = value
    return func


def build_replace(targets):
    """Get pointers to appropriate replace_function for a target.

    Parameters
    ----------
    targets : str or list of str
        targets to determine replace_function function pointers.

    Returns
    -------
    replace_funcs : function pointer or list of function pointers
        None is returned as the function pointer if the target string is
        not in the function name

    """
    if isinstance(targets, str):
        targets = [targets]

    # remove exe extension from targets
    for idx, target in enumerate(targets):
        if ".exe" in target.lower():
            targets[idx] = target[:-4]

    # get a dictionary of update functions
    funcs = get_function_names(sys.modules[__name__], select_name="update_")

    # generate a list of available functions
    replace_funcs = []
    for target in targets:
        f = None
        for key, value in funcs.items():
            if target in key:
                f = value
                break
        replace_funcs.append(f)

    # transform from a list to the function pointer if only one element
    # is in the list
    if len(replace_funcs) == 1:
        replace_funcs = replace_funcs[0]
    return replace_funcs


# routines for updating source files locations and to compile
# with gfortran, gcc, and g++
def update_triangle_files(srcdir, fc, cc, arch, double):
    """Update triangle source files.

    Parameters
    ----------
    srcdir : str
        path to directory with source files
    fc : str
        fortran compiler
    cc : str
        c/c++ compiler
    arch : str
        architecture
    double : bool
        boolean indicating if compiler switches are used to build a
        double precision target

    Returns
    -------

    """
    # move the downloaded files
    rootdir = os.path.join(*(srcdir.split(os.path.sep)[:1]))
    prog_dict = usgs_program_data().get_target("triangle")
    dirname = prog_dict.dirname
    dstpth = os.path.join(rootdir, dirname)

    # make destination directory
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)

    # make src directory
    if not os.path.exists(srcdir):
        os.makedirs(srcdir)

    # move the source files
    src = os.path.join(rootdir, "triangle.c")
    dst = os.path.join(srcdir, "triangle.c")
    shutil.move(src, dst)
    src = os.path.join(rootdir, "triangle.h")
    dst = os.path.join(srcdir, "triangle.h")
    shutil.move(src, dst)

    return


def update_mt3dms_files(srcdir, fc, cc, arch, double):
    """Update MT3DMS source files.

    Parameters
    ----------
    srcdir : str
        path to directory with source files
    fc : str
        fortran compiler
    cc : str
        c/c++ compiler
    arch : str
        architecture
    double : bool
        boolean indicating if compiler switches are used to build a
        double precision target

    Returns
    -------

    """
    # move the downloaded files
    rootdir = os.path.join(*(srcdir.split(os.path.sep)[:1]))
    prog_dict = usgs_program_data().get_target("mt3dms")
    dirname = prog_dict.dirname
    dstpth = os.path.join(rootdir, dirname)

    # Clean up unneeded files
    for f in ["ReadMe_MT3DMS.pdf", "upgrade.pdf"]:
        print('Removing..."{}"'.format(f))
        os.remove(os.path.join(rootdir, f))

    # remove some unneeded folders
    dir_list = ["bin", "doc", "examples", "utility"]
    for d in dir_list:
        dname = os.path.join(rootdir, d)
        if os.path.isdir(dname):
            print('Removing..."{}"'.format(dname))
            shutil.rmtree(dname)

    # make destination directory
    if not os.path.exists(dstpth):
        os.makedirs(dstpth)

    # move the files
    for src_dir, dirs, files in os.walk(rootdir):
        # skip target directory (dirname)
        if dirname in src_dir:
            continue
        if src_dir is rootdir:
            continue
        else:
            dst_dir = src_dir.replace(rootdir + os.path.sep, "")
            dst_dir = os.path.join(dstpth, dst_dir)
        if not os.path.exists(dst_dir):
            os.mkdir(dst_dir)
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)
            if os.path.exists(dst_file):
                os.remove(dst_file)
            print("{} -> {}".format(src_file, dst_dir))
            # shutil.copy(src_file, dst_dir)
            shutil.move(src_file, dst_file)

    # remove the original source directory
    dname = os.path.join(rootdir, "src")
    if os.path.isdir(dname):
        print('Removing..."{}"'.format(dname))
        shutil.rmtree(dname)

    # remove some unneeded files
    file_list = ["automake.fig", "mt3dms5b.exe"]
    for f in file_list:
        dname = os.path.join(srcdir, f)
        if os.path.isfile(dname):
            print('Removing..."{}"'.format(dname))
            os.remove(dname)

    # Replace the getcl command with getarg
    f1 = open(os.path.join(srcdir, "mt3dms5.for"), "r")
    f2 = open(os.path.join(srcdir, "mt3dms5.for.tmp"), "w")
    for line in f1:
        f2.write(line.replace("CALL GETCL(FLNAME)", "CALL GETARG(1,FLNAME)"))
    f1.close()
    f2.close()
    os.remove(os.path.join(srcdir, "mt3dms5.for"))
    shutil.move(
        os.path.join(srcdir, "mt3dms5.for.tmp"),
        os.path.join(srcdir, "mt3dms5.for"),
    )

    # Need to initialize the V array in SADV5B
    # see here: https://github.com/MODFLOW-USGS/mt3d-usgs/pull/46
    f1 = open(os.path.join(srcdir, "mt_adv5.for"), "r")
    f2 = open(os.path.join(srcdir, "mt_adv5.for.tmp"), "w")
    sfind = "C--SET DT TO NEGATIVE FOR BACKWARD TRACKING"
    sreplace = "C--INITIALIZE\n      V(:)=0.\nC\n" + sfind
    for line in f1:
        f2.write(line.replace(sfind, sreplace))
    f1.close()
    f2.close()
    os.remove(os.path.join(srcdir, "mt_adv5.for"))
    shutil.move(
        os.path.join(srcdir, "mt_adv5.for.tmp"),
        os.path.join(srcdir, "mt_adv5.for"),
    )

    for file_list in ["mt_btn5.for", "mt_utl5.for"]:
        fpth = os.path.join(srcdir, file_list)
        with open(fpth) as f:
            lines = f.readlines()
        f = open(fpth, "w")
        for line in lines:
            if "'FILESPEC.INC'" in line:
                line = line.replace("'FILESPEC.INC'", "'filespec.inc'")
            f.write(line)
        f.close()

    return


def update_swtv4_files(srcdir, fc, cc, arch, double):
    """Update SEAWAT source files

    Parameters
    ----------
    srcdir : str
        path to directory with source files
    fc : str
        fortran compiler
    cc : str
        c/c++ compiler
    arch : str
        architecture
    double : bool
        boolean indicating if compiler switches are used to build a
        double precision target

    Returns
    -------

    """
    # Remove the parallel and serial folders from the source directory
    dlist = ["parallel", "serial"]
    for d in dlist:
        dname = os.path.join(srcdir, d)
        if os.path.isdir(dname):
            print('Removing..."{}"'.format(dname))
            shutil.rmtree(os.path.join(srcdir, d))

    # rename all source files to lower case so compilation doesn't
    # bomb on case-sensitive operating systems
    srcfiles = os.listdir(srcdir)
    for filename in srcfiles:
        src = os.path.join(srcdir, filename)
        dst = os.path.join(srcdir, filename.lower())
        if "linux" in sys.platform.lower() or "darwin" in sys.platform.lower():
            os.rename(src, dst)

    if "linux" in sys.platform.lower() or "darwin" in sys.platform.lower():
        updfile = False
        if cc in ["icc", "clang", "gcc"]:
            updfile = True
        if updfile:
            fpth = os.path.join(srcdir, "gmg1.f")
            lines = [line.rstrip() for line in open(fpth)]
            f = open(fpth, "w")
            for line in lines:
                if (
                    "      !DEC$ ATTRIBUTES ALIAS:'_resprint' :: RESPRINT"
                    in line
                ):
                    line = (
                        "C      !DEC$ ATTRIBUTES ALIAS:'_resprint' :: RESPRINT"
                    )
                f.write("{}\n".format(line))
            f.close()
    else:
        # must be windows
        if arch == "intel64":
            fpth = os.path.join(srcdir, "gmg1.f")
            lines = [line.rstrip() for line in open(fpth)]
            f = open(fpth, "w")
            for line in lines:
                # comment out the 32 bit one and activate the 64 bit line
                if (
                    "C      !DEC$ ATTRIBUTES ALIAS:'resprint' :: RESPRINT"
                    in line
                ):
                    line = (
                        "       !DEC$ ATTRIBUTES ALIAS:'resprint' :: RESPRINT"
                    )
                if (
                    "      !DEC$ ATTRIBUTES ALIAS:'_resprint' :: RESPRINT"
                    in line
                ):
                    line = (
                        "C      !DEC$ ATTRIBUTES ALIAS:'_resprint' :: RESPRINT"
                    )
                f.write("{}\n".format(line))
            f.close()

    return


def update_mf2005_files(srcdir, fc, cc, arch, double):
    """Update MODFLOW2005 source files

    Parameters
    ----------
    srcdir : str
        path to directory with source files
    fc : str
        fortran compiler
    cc : str
        c/c++ compiler
    arch : str
        architecture
    double : bool
        boolean indicating if compiler switches are used to build a
        double precision target

    Returns
    -------

    """
    # update utl7.f
    tag = "IBINARY=0"
    fpth = os.path.join(srcdir, "utl7.f")
    with open(fpth) as f:
        lines = f.readlines()
    f = open(fpth, "w")
    for line in lines:
        if tag in line:
            indent = len(line) - len(line.lstrip())
            line += indent * " " + "JAUX=0\n"
        f.write(line)
    f.close()

    # update gwf2swi27.f
    tag = "INTEGER, PARAMETER :: VERSIZE ="
    prec = 4
    if double:
        prec = 8
    fpth = os.path.join(srcdir, "gwf2swi27.f")
    with open(fpth) as f:
        lines = f.readlines()
    f = open(fpth, "w")
    for line in lines:
        if line.lower()[0] not in ["!", "c"]:
            if tag in line:
                indent = len(line) - len(line.lstrip())
                line = indent * " " + tag + " {}\n".format(prec)
        f.write(line)
    f.close()

    # update gwf2swt7.f
    tag = "EST(J,I,N)=0.0"
    fpth = os.path.join(srcdir, "gwf2swt7.f")
    with open(fpth) as f:
        lines = f.readlines()
    f = open(fpth, "w")
    for line in lines:
        if tag in line:
            indent = len(line) - len(line.lstrip())
            line += indent * " " + "PCS(J,I,N)=0.0\n"
        f.write(line)
    f.close()


def update_mfnwt_files(srcdir, fc, cc, arch, double):
    """Update MODFLOW-NWT source files

    Parameters
    ----------
    srcdir : str
        path to directory with source files
    fc : str
        fortran compiler
    cc : str
        c/c++ compiler
    arch : str
        architecture
    double : bool
        boolean indicating if compiler switches are used to build a
        double precision target

    Returns
    -------

    """
    # update utl7.f
    fpth = os.path.join(srcdir, "utl7.f")
    tag = "IBINARY=0"
    with open(fpth) as f:
        lines = f.readlines()
    f = open(fpth, "w")
    for line in lines:
        if tag in line:
            indent = len(line) - len(line.lstrip())
            line += indent * " " + "JAUX=0\n"
        f.write(line)
    f.close()

    # update gwf2swt7.f
    tag = "EST(J,I,N)=0.0"
    fpth = os.path.join(srcdir, "gwf2swt7.f")
    if os.path.exists(fpth):
        with open(fpth) as f:
            lines = f.readlines()
        f = open(fpth, "w")
        for line in lines:
            if tag in line:
                indent = len(line) - len(line.lstrip())
                line += indent * " " + "PCS(J,I,N)=0.0\n"
            f.write(line)
        f.close()

    # remove lrestart.f
    fpth = os.path.join(srcdir, "Irestart.f")
    if os.path.exists(fpth):
        os.remove(fpth)

    # update gwf2swi27.f or gwf2swi27.f
    fpth = os.path.join(srcdir, "gwf2swi27.f")
    if not os.path.exists(fpth):
        fpth = os.path.join(srcdir, "gwf2swi27.fpp")
    if os.path.exists(fpth):
        tag = "(i,csolver(i),i=1,3)"
        new_tag = "(i,csolver(i),i=1,2)"
        with open(fpth) as f:
            lines = f.readlines()
        f = open(fpth, "w")
        for line in lines:
            if tag in line:
                line = line.replace(tag, new_tag)
            f.write(line)
        f.close()


def update_gsflow_files(srcdir, fc, cc, arch, double):
    """Update GSFLOW source files

    Parameters
    ----------
    srcdir : str
        path to directory with source files
    fc : str
        fortran compiler
    cc : str
        c/c++ compiler
    arch : str
        architecture
    double : bool
        boolean indicating if compiler switches are used to build a
        double precision target

    Returns
    -------

    """
    # update gwf2swt7.f
    tag = "EST(J,I,N)=0.0"
    fpth = os.path.join(srcdir, "modflow", "gwf2swt7.f")
    with open(fpth) as f:
        lines = f.readlines()
    f = open(fpth, "w")
    for line in lines:
        if tag in line:
            indent = len(line) - len(line.lstrip())
            line += indent * " " + "PCS(J,I,N)=0.0\n"
        f.write(line)
    f.close()

    # update gwf2swi27.f or gwf2swi27.fpp
    fpth = os.path.join(srcdir, "modflow", "gwf2swi27.f")
    if not os.path.exists(fpth):
        fpth = os.path.join(srcdir, "modflow", "gwf2swi27.fpp")
    if os.path.exists(fpth):
        tag = "(i,csolver(i),i=1,3)"
        new_tag = "(i,csolver(i),i=1,2)"
        with open(fpth) as f:
            lines = f.readlines()
        f = open(fpth, "w")
        for line in lines:
            if tag in line:
                line = line.replace(tag, new_tag)
            f.write(line)
        f.close()

    # remove merge and lib directories
    pths = [os.path.join(srcdir, "merge"), os.path.join(srcdir, "lib")]
    for pth in pths:
        if os.path.isdir(pth):
            shutil.rmtree(pth)

    # remove existing *.mod, *.o, and *.a (if any are left) files
    dpths = [
        os.path.join(srcdir, o)
        for o in os.listdir(srcdir)
        if os.path.isdir(os.path.join(srcdir, o))
    ]

    for dpth in dpths:
        for f in os.listdir(dpth):
            ext = os.path.splitext(f)[1]
            fpth = os.path.join(dpth, f)
            if ext in [".mod", ".o", ".a"]:
                os.remove(fpth)

    # edit and remove os specific files
    if sys.platform.lower() == "win32":
        if "ifort" not in fc:
            tag = "FORM='BINARY'"
            new_tag = "FORM='UNFORMATTED', ACCESS='STREAM'"
            fpth = os.path.join(srcdir, "prms", "utils_prms_windows.f90")
            with open(fpth) as f:
                lines = f.readlines()
            f = open(fpth, "w")
            for line in lines:
                if tag in line:
                    line = line.replace(tag, new_tag)
                f.write(line)
            f.close()

        fpths = [
            os.path.join(srcdir, "prms", "utils_prms_linux.f90"),
            os.path.join(srcdir, "prms", "utils_prms.f90"),
        ]
    else:
        fpths = [
            os.path.join(srcdir, "prms", "utils_prms_linux.f90"),
            os.path.join(srcdir, "prms", "utils_prms_windows.f90"),
        ]
    for fpth in fpths:
        os.remove(fpth)

    return


def update_mf2000_files(srcdir, fc, cc, arch, double):
    """Update MODFLOW-2000 source files

    Parameters
    ----------
    srcdir : str
        path to directory with source files
    fc : str
        fortran compiler
    cc : str
        c/c++ compiler
    arch : str
        architecture
    double : bool
        boolean indicating if compiler switches are used to build a
        double precision target

    Returns
    -------

    """
    # Remove six src folders
    dlist = ["beale2k", "hydprgm", "mf96to2k", "mfpto2k", "resan2k", "ycint2k"]
    for d in dlist:
        dname = os.path.join(srcdir, d)
        if os.path.isdir(dname):
            print('Removing..."{}"'.format(dname))
            shutil.rmtree(os.path.join(srcdir, d))

    # Move src files and serial src file to src directory
    tpth = os.path.join(srcdir, "mf2k")
    files = [
        f for f in os.listdir(tpth) if os.path.isfile(os.path.join(tpth, f))
    ]
    for f in files:
        shutil.move(os.path.join(tpth, f), os.path.join(srcdir, f))
    tpth = os.path.join(srcdir, "mf2k", "serial")
    files = [
        f for f in os.listdir(tpth) if os.path.isfile(os.path.join(tpth, f))
    ]
    for f in files:
        shutil.move(os.path.join(tpth, f), os.path.join(srcdir, f))

    # Remove mf2k directory in source directory
    tpth = os.path.join(srcdir, "mf2k")
    shutil.rmtree(tpth)

    # modify the openspec.inc file to use binary instead of unformatted
    fname = os.path.join(srcdir, "openspec.inc")
    with open(fname) as f:
        lines = f.readlines()
    with open(fname, "w") as f:
        for line in lines:
            if "      DATA FORM/'UNFORMATTED'/" in line:
                line = "C     DATA FORM/'UNFORMATTED'/\n"
            if "C      DATA FORM/'BINARY'/" in line:
                line = "       DATA FORM/'BINARY'/\n"
            f.write(line)
    return


def update_mflgr_files(srcdir, fc, cc, arch, double):
    """Update MODFLOW-LGR source files

    Parameters
    ----------
    srcdir : str
        path to directory with source files
    fc : str
        fortran compiler
    cc : str
        c/c++ compiler
    arch : str
        architecture
    double : bool
        boolean indicating if compiler switches are used to build a
        double precision target

    Returns
    -------

    """
    # update gwf2swt7.f
    tag = "EST(J,I,N)=0.0"
    fpth = os.path.join(srcdir, "gwf2swt7.f")
    with open(fpth) as f:
        lines = f.readlines()
    f = open(fpth, "w")
    for line in lines:
        if tag in line:
            indent = len(line) - len(line.lstrip())
            line += indent * " " + "PCS(J,I,N)=0.0\n"
        f.write(line)
    f.close()


def update_mp6_files(srcdir, fc, cc, arch, double):
    """Update MODPATH 6 source files

    Parameters
    ----------
    srcdir : str
        path to directory with source files
    fc : str
        fortran compiler
    cc : str
        c/c++ compiler
    arch : str
        architecture
    double : bool
        boolean indicating if compiler switches are used to build a
        double precision target

    Returns
    -------

    """
    fname1 = os.path.join(srcdir, "MP6Flowdata.for")
    f = open(fname1, "r")

    fname2 = os.path.join(srcdir, "MP6Flowdata_mod.for")
    f2 = open(fname2, "w")
    for line in f:
        line = line.replace("CD.QX2", "CD%QX2")
        f2.write(line)
    f.close()
    f2.close()
    os.remove(fname1)

    fname1 = os.path.join(srcdir, "MP6MPBAS1.for")
    f = open(fname1, "r")

    fname2 = os.path.join(srcdir, "MP6MPBAS1_mod.for")
    f2 = open(fname2, "w")
    for line in f:
        line = line.replace(
            "MPBASDAT(IGRID)%NCPPL=NCPPL", "MPBASDAT(IGRID)%NCPPL=>NCPPL"
        )
        f2.write(line)
    f.close()
    f2.close()
    os.remove(fname1)


def update_mp7_files(srcdir, fc, cc, arch, double):
    """Update MODPATH 7 source files

    Parameters
    ----------
    srcdir : str
        path to directory with source files
    fc : str
        fortran compiler
    cc : str
        c/c++ compiler
    arch : str
        architecture
    double : bool
        boolean indicating if compiler switches are used to build a
        double precision target

    Returns
    -------

    """
    fpth = os.path.join(srcdir, "StartingLocationReader.f90")
    with open(fpth) as f:
        lines = f.readlines()
    f = open(fpth, "w")
    for line in lines:
        if "pGroup%Particles(n)%InitialFace = 0" in line:
            continue
        f.write(line)
    f.close()


def update_vs2dt_files(srcdir, fc, cc, arch, double):
    """Update VS2DT source files

    Parameters
    ----------
    srcdir : str
        path to directory with source files
    fc : str
        fortran compiler
    cc : str
        c/c++ compiler
    arch : str
        architecture
    double : bool
        boolean indicating if compiler switches are used to build a
        double precision target

    Returns
    -------

    """
    # move the main source into the source directory
    f1 = os.path.join(srcdir, "..", "vs2dt3_3.f")
    f1 = os.path.abspath(f1)
    assert os.path.isfile(f1)
    f2 = os.path.join(srcdir, "vs2dt3_3.f")
    f2 = os.path.abspath(f2)
    shutil.move(f1, f2)
    assert os.path.isfile(f2)

    f1 = open(os.path.join(srcdir, "vs2dt3_3.f"), "r")
    f2 = open(os.path.join(srcdir, "vs2dt3_3.f.tmp"), "w")
    for line in f1:
        srctxt = "     `POSITION='REWIND')"
        rpctxt = "     `POSITION='REWIND',ACCESS='STREAM')"
        f2.write(line.replace(srctxt, rpctxt))
    f1.close()
    f2.close()
    os.remove(os.path.join(srcdir, "vs2dt3_3.f"))
    shutil.move(
        os.path.join(srcdir, "vs2dt3_3.f.tmp"),
        os.path.join(srcdir, "vs2dt3_3.f"),
    )

    return
