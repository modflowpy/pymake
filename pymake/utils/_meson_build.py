"""Private functions to build a target with the meson build system."""

import json
import os
from contextlib import contextmanager
from pathlib import Path

from ._compiler_language_files import (
    _get_c_files,
    _get_fortran_files,
    _get_main,
    _preprocess_file,
)
from ._compiler_switches import (
    _get_base_compiler_name,
    _get_c_flags,
    _get_fortran_flags,
    _get_linker_flags,
    _get_optlevel,
    _get_osname,
    _get_prepend,
)
from ._file_utils import _get_extrafiles_common_path
from .usgsprograms import usgs_program_data


@contextmanager
def _set_directory(path: Path):
    """Sets the cwd within the context.

    Parameters
    ----------
    path : Path
        path to the current working directory

    Returns
    -------
    None

    """
    origin = Path().absolute()
    try:
        Path(path).mkdir(exist_ok=True, parents=True)
        os.chdir(path)
        yield
    finally:
        os.chdir(origin)


def meson_build(
    mesondir,
    fc=None,
    cc=None,
    appdir=".",
    build_dir="_build",
    debug=None,
    fflags=None,
    cflags=None,
    syslibs=None,
):
    """Build executable(s) using the meson build system.

    Parameters
    ----------
    mesondir : str
        path to the main meson.build file
    fc : str
        fortran compiler (default is None, which will be the default system
        Fortran compiler)
    cc : str
        c or cpp compiler (default is None, which will be the default
        c/cpp compiler)
    appdir : str
        path where the executable(s) will be installed. (default is the
        current working directory)
    build_dir : str
        directory where meson build files are generated (default is _build)
    debug : bool
        boolean indicating if a debug executable will be built. the build
        type is left to the meson build file when None (default is None)
    fflags : list
        user provided list of fortran compiler flags (default is None)
    cflags : list
        user provided list of c or cpp compiler flags (default is None)
    syslibs : list
        user provided list of linker flags (default is None)

    Returns
    -------
    returncode : int
        return code

    """
    meson_test_path = Path(mesondir) / "meson.build"
    if meson_test_path.is_file():
        # setup meson
        returncode = meson_setup(
            mesondir,
            fc=fc,
            cc=cc,
            appdir=appdir,
            debug=debug,
            fflags=fflags,
            cflags=cflags,
            syslibs=syslibs,
        )
        # build and install executable(s) using meson
        if returncode == 0:
            returncode = meson_install(mesondir)
        else:
            print(
                "Could not run 'meson setup' using the meson build file "
                f"'{meson_test_path}'"
            )

        # return if setup and install were successful
        if returncode == 0:
            print(
                "\n\nBuilt executable(s) using the meson build file "
                f"'{meson_test_path}'"
            )
        else:
            print(
                "Could not run 'meson install' using the meson build file "
                f"'{meson_test_path}'"
            )
    else:
        returncode = 1

    return returncode


def meson_setup(
    mesondir,
    fc="gfortran",
    cc="gcc",
    appdir=".",
    build_dir="_build",
    debug=None,
    fflags=None,
    cflags=None,
    syslibs=None,
):
    """Run meson setup command.

    Parameters
    ----------
    mesondir : str
        path to the main meson.build file
    fc : str
        fortran compiler (default is None, which will be the default system
        Fortran compiler)
    cc : str
        c or cpp compiler (default is None, which will be the default
        c/cpp compiler)
    appdir : str
        path where the executable(s) will be installed. (default is the
        current working directory)
    build_dir : str
        directory where meson build files are generated (default is _build)
    debug : bool
        boolean indicating if a debug executable will be built. the build
        type is left to the meson build file when None (default is None)
    fflags : list
        user provided list of fortran compiler flags (default is None)
    cflags : list
        user provided list of c or cpp compiler flags (default is None)
    syslibs : list
        user provided list of linker flags (default is None)

    Returns
    -------
    returncode : int
        return code

    """
    # initialize the return code
    returncode = 0

    with _set_directory(mesondir):
        command_list = []
        if fc is not None:
            fc_env = os.environ.get("FC")
            if fc_env is not None:
                if fc != fc_env:
                    if _get_osname() == "win32":
                        os.environ["FC"] = fc
                    else:
                        command_list.append(f"FC={fc}")
            else:
                if _get_osname() == "win32":
                    os.environ["FC"] = fc
                else:
                    command_list.append(f"FC={fc}")
        if cc is not None:
            if _get_base_compiler_name(cc) in ("g++", "clang++"):
                cc_env = os.environ.get("CXX")
                if cc_env is not None:
                    if cc_env != cc:
                        if _get_osname() == "win32":
                            os.environ["CCX"] = cc
                        else:
                            command_list.append(f"CXX={cc}")
                else:
                    if _get_osname() == "win32":
                        os.environ["CCX"] = cc
                    else:
                        command_list.append(f"CXX={cc}")
            else:
                cc_env = os.environ.get("CC")
                if cc_env is not None:
                    if cc_env != cc:
                        if _get_osname() == "win32":
                            os.environ["CC"] = cc
                        else:
                            command_list.append(f"CC={cc}")
                else:
                    if _get_osname() == "win32":
                        os.environ["CC"] = cc
                    else:
                        command_list.append(f"CC={cc}")

        command_list.append("meson")
        command_list.append("setup")
        command_list.append(build_dir)

        if _get_osname() == "win32":
            command_list.append("--prefix=%CD%")
        else:
            command_list.append("--prefix=$(pwd)")

        libdir = os.path.relpath(os.path.abspath(appdir), os.path.abspath(mesondir))
        command_list.append(f"--libdir={libdir}")
        command_list.append(f"--bindir={libdir}")

        # the build type is only set for a meson build file pymake did not
        # generate, because a generated one sets the optimization and debug
        # options itself and a build type on the command line overrides them
        if debug is not None:
            command_list.append(f"--buildtype={'debug' if debug else 'release'}")

        # pass the flags the user asked for to the meson build file. the
        # flags for a language the build file does not use are ignored
        for option, flags in (
            ("fortran_args", fflags),
            ("c_args", cflags),
            ("fortran_link_args", syslibs),
            ("c_link_args", syslibs),
        ):
            if flags:
                if isinstance(flags, str):
                    flags = flags.split()
                command_list.append(f"-D{option}={' '.join(flags)}")

        if Path(build_dir).is_dir():
            command_list.append("--wipe")

        command = " ".join(command_list)
        print(f"\n{command}\n")

        returncode = os.system(command)

        # evaluate return code
        if returncode != 0:
            print(f"meson setup failed on '{command}'")

    return returncode


def meson_install(
    mesondir,
    build_dir="_build",
):
    """Run meson install command.

    Parameters
    ----------
    mesondir : str
        path to the main meson.build file
    build_dir : str
        directory where meson build files are generated (default is _build)
    debug : bool
        boolean indicating if a debug executable will be built. the build
        type is left to the meson build file when None (default is None)
    fflags : list
        user provided list of fortran compiler flags (default is None)
    cflags : list
        user provided list of c or cpp compiler flags (default is None)
    syslibs : list
        user provided list of linker flags (default is None)

    Returns
    -------
    returncode : int
        return code

    """
    # initialize the return code
    returncode = 0

    with _set_directory(mesondir):
        command_list = ["meson", "install", "-C", f"{build_dir}"]
        command = " ".join(command_list)
        print(f"\n{command}\n")
        returncode = os.system(command)

        # evaluate return code
        if returncode != 0:
            print(f"meson install failed on '{command}'")

    return returncode


def _rename_provided_target(mesondir, target, build_dir="_build"):
    """Rename the executable a provided meson build file installed.

    A meson build file a target provides names the executable it builds, and
    the name is not always the name of the target. mt3d-usgs builds mt3dusg
    rather than mt3dusgs, so the target that was asked for is never produced.
    The installed file is renamed when the target does not exist and the
    build installed a single file, so that the file to rename is not in
    doubt.

    Parameters
    ----------
    mesondir : str
        path to the main meson.build file
    target : str
        path for the executable that was asked for
    build_dir : str
        directory where meson build files are generated (default is _build)

    Returns
    -------

    """
    exe = Path(target)
    if exe.is_file():
        return

    # meson writes what it installed to the build directory, so the file to
    # rename does not have to be guessed from the directory it was put in
    intro = Path(mesondir) / build_dir / "meson-info" / "intro-installed.json"
    try:
        installed = [Path(pth) for pth in json.loads(intro.read_text()).values()]
    except (OSError, json.JSONDecodeError):
        return

    if len(installed) != 1:
        return

    built = installed[0]
    if built.is_file() and built.name != exe.name:
        print(f"renaming...'{built.name}' to '{exe.name}'")
        built.replace(exe)


def _meson_build(
    target,
    srcdir,
    srcdir2,
    extrafiles,
    srcfiles,
    debug,
    double,
    fc,
    cc,
    fflags,
    cflags,
    syslibs,
    sharedobject,
    mesondir,
    verbose,
):
    """Build the target using meson.

    Parameters
    ----------
    target : str
        path for executable to create
    srcdir : str
        path for directory containing source files
    srcdir2 : str
        additional directory with common source files.
    extrafiles : str
        path for extrafiles file that contains paths to additional source
        files to include
    srcfiles : list
        list of source file names
    debug : bool
        boolean indicating is a debug executable will be built
    double : bool
        boolean indicating a compiler switch will be used to create an
        executable with double precision real variables.
    fc : str
        fortran compiler
    cc : str
        c or cpp compiler
    fflags : list
        user provided list of fortran compiler flags
    cflags : list
        user provided list of c or cpp compiler flags
    syslibs : list
        user provided syslibs
    sharedobject : bool
        boolean indicating a shared object will be built
    mesondir : str
        Main meson.build file path
    verbose : bool
        boolean indicating if output will be printed to the terminal

    Returns
    -------
    returncode : int
        returncode

    """
    # use existing build file if it already exists
    returncode = meson_build(
        mesondir,
        fc=fc,
        cc=cc,
        appdir=Path(target).parent,
        debug=debug,
        fflags=fflags,
        cflags=cflags,
        syslibs=syslibs,
    )
    if returncode == 0:
        _rename_provided_target(mesondir, target)
        return returncode

    # create meson files
    # create dictionary with source file paths
    source_path_dict = {"main": srcdir}
    if srcdir2 is not None:
        source_path_dict["additional_srcdir"] = srcdir2

    common_path = _get_extrafiles_common_path(extrafiles)
    if common_path is not None:
        source_path_dict["extra"] = common_path

    # write meson.build files with directories in each source directory
    _create_source_meson_build(source_path_dict, srcfiles)

    # write main meson.build file
    _, fc_meson, cc_meson = _create_main_meson_build(
        mesondir,
        target,
        srcfiles,
        debug,
        double,
        fc,
        cc,
        fflags,
        cflags,
        syslibs,
        sharedobject,
        source_path_dict,
        verbose,
    )

    # setup meson and build
    return meson_build(
        mesondir,
        fc=fc_meson,
        cc=cc_meson,
        appdir=Path(target).parent,
    )


def _meson_path(pth):
    """Format a path so that it can be written to a meson build file.

    A meson build file is read as text, so a Windows separator starts an
    escape sequence, and a source directory such as 'true-binary' becomes a
    tab. Meson accepts a forward slash on every platform.

    Parameters
    ----------
    pth : str or Path
        path to format

    Returns
    -------
    pth : str
        path with a forward slash separator

    """
    return Path(pth).as_posix()


def _get_include_dirs(source_path_dict, mesondir):
    """Get the directories that contain c or c++ header files.

    Parameters
    ----------
    source_path_dict : dict
        dictionary with root directories containing source files. keys
        can be 'main', 'additional_srcdir', and 'extra' which correspond
        to the three possible locations of source files.
    mesondir : str
        Main meson.build file path

    Returns
    -------
    include_dirs : list
        paths of the directories that contain a header file, relative to
        mesondir

    """
    include_dirs = []
    for value in source_path_dict.values():
        header_dirs = {
            header.parent
            for pattern in ("*.h", "*.hpp")
            for header in Path(value).rglob(pattern)
            if header.is_file()
        }
        # sorted so the include directories are written to the meson build
        # file in the same order on every run, rather than the order the
        # file system happens to return them in
        for header_dir in sorted(header_dirs):
            include_dirs.append(_meson_path(os.path.relpath(header_dir, mesondir)))

    return include_dirs


def _create_main_meson_build(
    mesondir,
    target,
    srcfiles,
    debug,
    double,
    fc,
    cc,
    fflags,
    cflags,
    syslibs,
    sharedobject,
    source_path_dict,
    verbose,
):
    """Create the main meson build file.

    Parameters
    ----------
    mesondir
    target
    srcfiles
    debug
    double
    fc
    cc
    fflags
    cflags
    syslibs
    sharedobject
    source_path_dict
    verbose

    Parameters
    ----------
    mesondir : str
        Main meson.build file path
    target : str
        path for executable to create
    srcfiles : list
        list of source file names
    debug : bool
        boolean indicating is a debug executable will be built
    double : bool
        boolean indicating a compiler switch will be used to create an
        executable with double precision real variables.
    fc : str
        fortran compiler
    cc : str
        c or cpp compiler
    fflags : list
        user provided list of fortran compiler flags
    cflags : list
        user provided list of c or cpp compiler flags
    syslibs : list
        user provided syslibs
    sharedobject : bool
        boolean indicating a shared object will be built
    source_path_dict : dict
        dictionary with root directories containing source files. keys
        can be 'main', 'additional_srcdir', and 'extra' which correspond
        to the three possible locations of source files.
    verbose : bool
        boolean indicating if output will be printed to the terminal

    Returns
    -------
    main_meson_file : str
        path for main meson.build file
    fc_meson : str
        fortran compiler that meson will use. None if no fortran source files
    cc_meson : str
        c/cpp compiler that meson will use. None if no c/cpp source files

    """
    appdir = _meson_path(os.path.relpath(Path(target).parent, mesondir))
    target = Path(target).stem
    osname = _get_osname()

    # get target version number
    try:
        target_version = usgs_program_data.get_version(target)
    except:
        target_version = None

    # get main program file from list of source files
    mainfile = _get_main(srcfiles)

    # get list of unique fortran and c/c++ file extensions
    fext = _get_fortran_files(srcfiles, extensions=True)
    cext = _get_c_files(srcfiles, extensions=True)

    # remove main program file from source files and set linker language
    linker_language = None
    if mainfile is None:
        linker_language = "fortran"
    else:
        main_ext = Path(mainfile).suffix.lower()
        if fext is not None:
            if main_ext in fext:
                linker_language = "fortran"
        if linker_language is None:
            if cext is not None:
                if main_ext == ".c":
                    linker_language = "c"
                elif main_ext == ".cpp":
                    linker_language = "cpp"
    if linker_language is not None:
        linker_flags_meson = _get_linker_flags(
            target,
            fc,
            cc,
            syslibs,
            srcfiles,
            sharedobject=sharedobject,
            verbose=verbose,
        )
    else:
        raise ValueError("linker language not defined")

    # set source languages
    languages = []
    fc_meson = None
    fflags_meson = None
    if fext is not None:
        languages.append("fortran")
        fc_meson = fc
        fflags_meson = _get_fortran_flags(
            target,
            fc,
            fflags,
            debug,
            double=double,
            sharedobject=sharedobject,
            verbose=verbose,
        )
        if osname == "win32" and _get_base_compiler_name(fc) in ("ifort",):
            meson_ext_flag = False
        else:
            meson_ext_flag = True
        preprocess = _preprocess_file(srcfiles, meson=meson_ext_flag)
        if preprocess:
            if _get_base_compiler_name(fc) == "gfortran":
                fflags_meson.append("-cpp")
            else:
                prepend = _get_prepend(_get_base_compiler_name(fc), _get_osname())
                fflags_meson.append(f"{prepend}fpp")
    cc_meson = None
    cflags_meson = None
    if cext is not None:
        cc_meson = cc
        if ".cpp" in cext:
            languages.append("cpp")
        else:
            languages.append("c")
        cflags_meson = _get_c_flags(
            target,
            cc,
            cflags,
            debug,
            srcfiles=srcfiles,
            sharedobject=sharedobject,
            verbose=verbose,
        )

    # optimization level
    optlevel = _get_optlevel(target, fc, cc, debug, fflags, cflags)
    optlevel_int = int(optlevel.replace("-O", "").replace("/O", ""))

    main_meson_file = Path(mesondir) / "meson.build"
    if verbose:
        print(f"Creating main meson.build file {main_meson_file}")
    with open(main_meson_file, "w") as f:
        line = f"project(\n\t'{target}',\n"
        for language in languages:
            line += f"\t'{language}',\n"
        if target_version is not None:
            line += f"\tversion: '{target_version}',\n"
        line += "\tmeson_version: '>= 1.1.0',\n"
        line += "\tdefault_options: [\n\t\t'b_vscrt=static_from_buildtype',\n"
        line += f"\t\t'optimization={optlevel_int}',\n"
        line += "\t\t'debug="
        if debug:
            line += "true',\n"
        else:
            line += "false',\n"
        if target in ("mf6", "libmf6", "zbud6"):
            line += "\t\t'fortran_std=f2008'\n"
        line += "\t])\n\n"
        f.write(line)

        line = "if get_option('optimization') >= '2'\n"
        line += "\tprofile = 'release'\n"
        line += "else\n"
        line += "\tprofile = 'develop'\n"
        line += "endif\n\n"
        f.write(line)

        line = ""
        if "fortran" in languages:
            line += "fc = meson.get_compiler('fortran')\n"
            line += "fc_id = fc.get_id()\n"
            line += "fc_compile_args = [\n"
            for flag in fflags_meson:
                line += f"\t'{flag}',\n"
            line += "]\n"
        if cflags_meson is not None:
            if "cpp" in languages:
                line += "cc = meson.get_compiler('cpp')\n"
            else:
                line += "cc = meson.get_compiler('c')\n"
            line += "cc_id = cc.get_id()\n"
            line += "cc_compile_args = [\n"
            for flag in cflags_meson:
                line += f"\t'{flag}',\n"
            line += "]\n"
        line += "link_args = [\n"
        for flag in linker_flags_meson[1]:
            line += f"\t'{flag}',\n"
        line += "]\n"
        line += "sources = []\n\n"
        f.write(line)

        line = ""
        for language in languages:
            if language == "fortran":
                compiler_abbr = "fc"
            else:
                compiler_abbr = "cc"
            line += (
                "add_project_arguments("
                f"{compiler_abbr}.get_supported_arguments("
                f"{compiler_abbr}_compile_args), "
                f"language: '{language}')\n"
            )
        if linker_language == "fortran":
            linker_abbr = "fc"
        else:
            linker_abbr = "cc"
        line += "add_project_link_arguments("
        line += f"{linker_abbr}.get_supported_arguments(link_args), "
        line += f"language: '{linker_language}')\n\n"
        f.write(line)

        # add source directories
        line = ""
        for key, value in source_path_dict.items():
            pth = _meson_path(os.path.relpath(value, mesondir))
            line += f"subdir('{pth}')\n"
        line += "\n"
        f.write(line)

        # get list of include directories
        include_text = ""
        if "cpp" in languages or "c" in languages:
            include_dirs = _get_include_dirs(source_path_dict, mesondir)
            if len(include_dirs) > 0:
                include_text = ", include_directories : incdir"
                line = "incdir = include_directories(\n"
                for include_dir in include_dirs:
                    line += f"\t'{include_dir}',\n"
                line += ")\n\n"
                f.write(line)

        # add build command
        # meson links a target that has both c and fortran sources with the
        # c compiler, and a fortran main is left in the fortran runtime by
        # some compilers, so the language that has the main program links
        if sharedobject:
            line = (
                f"library('{target}', sources{include_text}"
                ", install: true, name_prefix: '', "
                f"link_language: '{linker_language}', "
                f"install_dir: '{appdir}')\n\n"
            )
        else:
            line = (
                f"executable('{target}', sources{include_text}"
                f", link_language: '{linker_language}'"
                f", install: true, install_dir: '{appdir}')\n\n"
            )
        f.write(line)

    return main_meson_file, fc_meson, cc_meson


def _create_source_meson_build(source_path_dict, srcfiles):
    """Create meson.build files with a list of source files in the root of
    each source file location defined in source_path_dict.

    Parameters
    ----------
    source_path_dict : dict
        dictionary with root directories containing source files. keys
        can be 'main', 'additional_srcdir', and 'extra' which correspond
        to the three possible locations of source files.
    srcfiles : list
        list of source file names

    Returns
    -------
    None

    """
    # create a copy so original srcfiles list is not modified
    srcfiles_copy = srcfiles.copy()

    # iterate over the files in each source directory
    for key, value in source_path_dict.items():
        with open(Path(value) / "meson.build", "w") as f:
            f.write("sources += files(\n")
            pop_list = []
            for source_file in srcfiles_copy:
                if os.path.relpath(value) in source_file:
                    pth = os.path.relpath(source_file, start=value)
                    temp_list = Path(pth).parts
                    line = f"\t\t'{temp_list[0]}'"
                    for temp in temp_list[1:]:
                        line += f" / '{temp}'"
                    f.write(f"{line},\n")
                    pop_list.append(source_file)
            f.write(")\n\n")

            # remove assigned source files
            for temp in pop_list:
                srcfiles_copy.remove(temp)

    return
