import os
import sys
import shutil
import platform
import types

from .pymake import main
from .download import download_and_unzip
from .usgsurls import usgs_prog_data


def get_function_names(module, select_name=None):
    """
    Get a dictionary of functions available in a user-specified source file.
    This function was developed to create a dictionary of functions in this
    source file (build_program.py). Optionally, the user can get a get a
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
        if type(value) is types.FunctionType:
            if select_name is None:
                ladd = True
            else:
                if select_name in value.__name__:
                    ladd = True
            if ladd:
                func[value.__name__] = value
    return func


def build_program(target='mf2005', fc='gfortran', cc='gcc', makeclean=True,
                  expedite=False, dryrun=False, double=False, debug=False,
                  include_subdirs=False, fflags=None, arch='intel64',
                  makefile=False, srcdir2=None, extrafiles=None,
                  exe_name=None, exe_dir=None,
                  replace_function=None, verify=True, modify_exe_name=True,
                  download_dir=None, download=True,
                  download_clean=False, download_verify=True, timeout=30):
    """

    Parameters
    ----------
    target : str

    fc : str
    cc : str
    makeclean : bool
    expedite : bool
    dryrun : bool
    double : bool
    debug : bool
    include_subdirs : bool
    fflags : str or list
    arch : str
    makefile : bool
    srcdir2 : str
    extrafiles : str
    exe_name : str
    exe_dir : str
    replace_function : str
    verify : bool
    modify_exe_name : bool
    download_dir : str
    download : bool
    download_clean : bool
    download_verify : bool
    timeout : int

    Returns
    -------

    """
    # set exe_name
    if exe_name is None:
        exe_name = target

    if modify_exe_name:
        if double:
            filename, file_extension = os.path.splitext(exe_name)
            if 'dbl' not in filename.lower():
                exe_name = filename + 'dbl' + file_extension
        if debug:
            filename, file_extension = os.path.splitext(exe_name)
            if filename.lower()[-1] != 'd':
                exe_name = filename + 'd' + file_extension

    if platform.system().lower() == 'windows':
        filename, file_extension = os.path.splitext(exe_name)
        if file_extension.lower() is not '.exe':
            exe_name += '.exe'

    if exe_dir is not None:
        exe_name = os.path.abspath(os.path.join(exe_dir, exe_name))

    # extract program data for target
    prog_dict = usgs_prog_data.get_target(target)

    # set url
    url = prog_dict.url

    # Set dir name
    dirname = prog_dict.dirname
    if download_dir is None:
        dirname = './'
        download_dir = './'
    else:
        dirname = os.path.join(download_dir, dirname)

    # make the download directory if it does not exist
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    # Set srcdir name
    srcdir = prog_dict.srcdir
    srcdir = os.path.join(dirname, srcdir)

    # Download the distribution
    if download:
        download_and_unzip(url, pth=download_dir, verify=download_verify,
                           timeout=timeout)

    if replace_function is not None:
        print('replacing select source files for {}'.format(target))
        replace_function(srcdir, fc, cc, arch)

    # compile code
    print('compiling...{}'.format(os.path.relpath(exe_name)))
    main(srcdir, exe_name, fc=fc, cc=cc, makeclean=makeclean,
         expedite=expedite, dryrun=dryrun, double=double, debug=debug,
         include_subdirs=include_subdirs, fflags=fflags, arch=arch,
         makefile=makefile, srcdir2=srcdir2, extrafiles=extrafiles)

    if verify:
        app = os.path.relpath(exe_name)
        msg = '{} does not exist.'.format(app)
        assert os.path.isfile(exe_name), msg

    # clean download directory if different than directory with executable
    if download_clean:
        edir = os.path.abspath(os.path.dirname(exe_name))
        ddir = os.path.abspath(download_dir)
        if edir != ddir:
            if os.path.isdir(ddir):
                shutil.rmtree(ddir)

    return


def build_targets(current=True):
    """
    Build a list of targets

    Parameters
    ----------
    current : bool
        return list of current targets. If current is False, returned list
        will include all available USGS applications included in usgsurls.txt.
        Default is True

    Returns
    -------
    targets : list
        list of targets

    """
    return usgs_prog_data.get_keys(current=current)


def build_replace(targets):
    """
    Get pointers to appropriate replace_function for a target

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

    # get a dictionary of update functions
    funcs = get_function_names(sys.modules[__name__], select_name='update_')

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


# routines for updating source files to compile with gfortran
def update_mt3dfiles(srcdir, fc, cc, arch):
    """
    Update the MT3D source files

    Parameters
    ----------
    srcdir : str
    fc : str
    cc : str
    arch : str

    Returns
    -------

    """
    # move the downloaded files
    rootdir = os.path.join(*(srcdir.split(os.path.sep)[:1]))
    prog_dict = usgs_prog_data().get_target('mt3dms')
    dirname = prog_dict.dirname
    dstpth = os.path.join(rootdir, dirname)

    # Clean up unneeded files
    for f in ['ReadMe_MT3DMS.pdf', 'upgrade.pdf']:
        print('Removing {}'.format(f))
        os.remove(os.path.join(rootdir, f))

    # remove some unneeded folders
    dir_list = ['bin', 'doc', 'examples', 'utility']
    for d in dir_list:
        dname = os.path.join(rootdir, d)
        if os.path.isdir(dname):
            print('Removing...', dname)
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
            dst_dir = src_dir.replace(rootdir + os.path.sep, '')
            dst_dir = os.path.join(dstpth, dst_dir)
        if not os.path.exists(dst_dir):
            os.mkdir(dst_dir)
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)
            if os.path.exists(dst_file):
                os.remove(dst_file)
            print('{} -> {}'.format(src_file, dst_dir))
            # shutil.copy(src_file, dst_dir)
            shutil.move(src_file, dst_dir)

    # remove the original source directory
    dname = os.path.join(rootdir, 'src')
    if os.path.isdir(dname):
        print('Removing...', dname)
        shutil.rmtree(dname)

    # remove some unneeded files
    file_list = ['automake.fig', 'mt3dms5b.exe']
    for f in file_list:
        dname = os.path.join(srcdir, f)
        if os.path.isfile(dname):
            print('Removing ', dname)
            os.remove(dname)

    # Replace the getcl command with getarg
    f1 = open(os.path.join(srcdir, 'mt3dms5.for'), 'r')
    f2 = open(os.path.join(srcdir, 'mt3dms5.for.tmp'), 'w')
    for line in f1:
        f2.write(line.replace('CALL GETCL(FLNAME)', 'CALL GETARG(1,FLNAME)'))
    f1.close()
    f2.close()
    os.remove(os.path.join(srcdir, 'mt3dms5.for'))
    shutil.move(os.path.join(srcdir, 'mt3dms5.for.tmp'),
                os.path.join(srcdir, 'mt3dms5.for'))

    return


def update_seawatfiles(srcdir, fc, cc, arch):
    # Remove the parallel and serial folders from the source directory
    dlist = ['parallel', 'serial']
    for d in dlist:
        dname = os.path.join(srcdir, d)
        if os.path.isdir(dname):
            print('Removing ', dname)
            shutil.rmtree(os.path.join(srcdir, d))

    # rename all source files to lower case so compilation doesn't
    # bomb on case-sensitive operating systems
    srcfiles = os.listdir(srcdir)
    for filename in srcfiles:
        src = os.path.join(srcdir, filename)
        dst = os.path.join(srcdir, filename.lower())
        if 'linux' in sys.platform or 'darwin' in sys.platform:
            os.rename(src, dst)

    if 'linux' in sys.platform or 'darwin' in sys.platform:
        updfile = False
        if 'icc' in cc or 'clang' in cc:
            updfile = True
        if updfile:
            fpth = os.path.join(srcdir, 'gmg1.f')
            lines = [line.rstrip() for line in open(fpth)]
            f = open(fpth, 'w')
            for line in lines:
                if "      !DEC$ ATTRIBUTES ALIAS:'_resprint' :: RESPRINT" in line:
                    line = "C      !DEC$ ATTRIBUTES ALIAS:'_resprint' :: RESPRINT"
                f.write('{}\n'.format(line))
            f.close()
    else:
        # must be windows
        if arch == 'intel64':
            fpth = os.path.join(srcdir, 'gmg1.f')
            lines = [line.rstrip() for line in open(fpth)]
            f = open(fpth, 'w')
            for line in lines:
                # comment out the 32 bit one and activate the 64 bit line
                if "C      !DEC$ ATTRIBUTES ALIAS:'resprint' :: RESPRINT" in line:
                    line = "       !DEC$ ATTRIBUTES ALIAS:'resprint' :: RESPRINT"
                if "      !DEC$ ATTRIBUTES ALIAS:'_resprint' :: RESPRINT" in line:
                    line = "C      !DEC$ ATTRIBUTES ALIAS:'_resprint' :: RESPRINT"
                f.write('{}\n'.format(line))
            f.close()

    return


def update_mf2000files(srcdir, fc, cc, arch):
    # Remove six src folders
    dlist = ['beale2k', 'hydprgm', 'mf96to2k', 'mfpto2k', 'resan2k', 'ycint2k']
    for d in dlist:
        dname = os.path.join(srcdir, d)
        if os.path.isdir(dname):
            print('Removing ', dname)
            shutil.rmtree(os.path.join(srcdir, d))

    # Move src files and serial src file to src directory
    tpth = os.path.join(srcdir, 'mf2k')
    files = [f for f in os.listdir(tpth) if
             os.path.isfile(os.path.join(tpth, f))]
    for f in files:
        shutil.move(os.path.join(tpth, f), srcdir)
    tpth = os.path.join(srcdir, 'mf2k', 'serial')
    files = [f for f in os.listdir(tpth) if
             os.path.isfile(os.path.join(tpth, f))]
    for f in files:
        shutil.move(os.path.join(tpth, f), srcdir)

    # Remove mf2k directory in source directory
    tpth = os.path.join(srcdir, 'mf2k')
    shutil.rmtree(tpth)


def update_mp6files(srcdir, fc, cc, arch):
    fname1 = os.path.join(srcdir, 'MP6Flowdata.for')
    f = open(fname1, 'r')

    fname2 = os.path.join(srcdir, 'MP6Flowdata_mod.for')
    f2 = open(fname2, 'w')
    for line in f:
        line = line.replace('CD.QX2', 'CD%QX2')
        f2.write(line)
    f.close()
    f2.close()
    os.remove(fname1)

    fname1 = os.path.join(srcdir, 'MP6MPBAS1.for')
    f = open(fname1, 'r')

    fname2 = os.path.join(srcdir, 'MP6MPBAS1_mod.for')
    f2 = open(fname2, 'w')
    for line in f:
        line = line.replace('MPBASDAT(IGRID)%NCPPL=NCPPL',
                            'MPBASDAT(IGRID)%NCPPL=>NCPPL')
        f2.write(line)
    f.close()
    f2.close()
    os.remove(fname1)


def update_mp7files(srcdir, fc, cc, arch):
    fpth = os.path.join(srcdir, 'StartingLocationReader.f90')
    with open(fpth) as f:
        lines = f.readlines()
    f = open(fpth, 'w')
    for line in lines:
        if 'pGroup%Particles(n)%InitialFace = 0' in line:
            continue
        f.write(line)
    f.close()


def update_mf6files(srcdir, fc, cc, arch):
    fpth = os.path.join(srcdir, 'Solution', 'NumericalSolution.f90')
    with open(fpth) as f:
        lines = f.readlines()
    f = open(fpth, 'w')
    for idx, line in enumerate(lines):
        if "case ('NO_PTC')" in line:
            if lines[idx + 1].strip() == 'call this%parser%DevOpt()':
                lines[idx + 1] = lines[idx + 1].replace('call', '!call')
        f.write(line)
    f.close()


def update_vs2dtfiles(srcdir, fc, cc, arch):
    # move the main source into the source directory
    f1 = os.path.join(srcdir, '..', 'vs2dt3_3.f')
    f1 = os.path.abspath(f1)
    assert os.path.isfile(f1)
    f2 = os.path.join(srcdir, 'vs2dt3_3.f')
    f2 = os.path.abspath(f2)
    shutil.move(f1, f2)
    assert os.path.isfile(f2)

    f1 = open(os.path.join(srcdir, 'vs2dt3_3.f'), 'r')
    f2 = open(os.path.join(srcdir, 'vs2dt3_3.f.tmp'), 'w')
    for line in f1:
        srctxt = "     `POSITION='REWIND')"
        rpctxt = "     `POSITION='REWIND',ACCESS='STREAM')"
        f2.write(line.replace(srctxt, rpctxt))
    f1.close()
    f2.close()
    os.remove(os.path.join(srcdir, 'vs2dt3_3.f'))
    shutil.move(os.path.join(srcdir, 'vs2dt3_3.f.tmp'),
                os.path.join(srcdir, 'vs2dt3_3.f'))

    return
