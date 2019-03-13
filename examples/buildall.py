# Build the executables that are used in the flopy autotests
import os
import sys

try:
    import pymake
except:
    print('pymake is not installed...will not build executables')
    pymake = None

fc = 'gfortran'
cc = 'gcc'

# bindir should be in the user path to run flopy tests with appropriate
# executables
#


# by default bindir will be in user directory unless --root command
# line argument is passed
# On windows will be C:\\Users\\username\\.local\\bin
# On linux and osx will be /Users/username/.local/bin
bindir = None
for idx, arg in enumerate(sys.argv):
    if '--root' in arg.lower():
        bindir = '.'
    elif '--appdir' in arg.lower():
        bindir = sys.argv[idx + 1]
        if not os.path.isdir(bindir):
            os.mkdir(bindir)
if bindir is None:
    bindir = os.path.join(os.path.expanduser('~'), '.local', 'bin')
    bindir = os.path.abspath(bindir)
if not os.path.isdir(bindir):
    bindir = '.'
print('targets will be placed the directory:\n    {}\n'.format(bindir))


def set_compiler(target):
    fct = fc
    cct = cc
    # parse command line arguments to see if user specified options
    # relative to building the target
    msg = ''
    for idx, arg in enumerate(sys.argv):
        if arg.lower() == '--ifort':
            if len(msg) > 0:
                msg += '\n'
            msg += '{} - '.format(arg.lower()) + \
                   '{} will be built with ifort.'.format(target)
            fct = 'ifort'
        elif arg.lower() == '--icc':
            if len(msg) > 0:
                msg += '\n'
            msg += '{} - '.format(arg.lower()) + \
                   '{} will be built with icc.'.format(target)
            cct = 'icc'
        elif arg.lower() == '--cl':
            if len(msg) > 0:
                msg += '\n'
            msg += '{} - '.format(arg.lower()) + \
                   '{} will be built with cl.'.format(target)
            cct = 'cl'
        elif arg.lower() == '--clang':
            if len(msg) > 0:
                msg += '\n'
            msg += '{} - '.format(arg.lower()) + \
                   '{} will be built with clang.'.format(target)
            cct = 'clang'
    if len(msg) > 0:
        print(msg)

    return fct, cct


def set_double(target):
    double = False
    for idx, arg in enumerate(sys.argv):
        if arg.lower() == '-dbl' or arg.lower() == '--double':
            double = True
            break

    # write a message
    if double:
        msg = '{} will be built using double precision floats.'.format(target)
    else:
        msg = '{} will be built using single precision floats.'.format(target)
    print(msg)

    return double


def set_debug(target):
    debug = False
    for idx, arg in enumerate(sys.argv):
        if arg.lower() == '-dbg' or arg.lower() == '--debug':
            debug = True
            break

    # write a message
    if debug:
        msg = '{} will be built with debug flags.'.format(target)
    else:
        msg = '{} will be built as a release application.'.format(target)
    print(msg)

    return debug


def set_arch(target):
    arch = 'intel64'
    for idx, arg in enumerate(sys.argv):
        if arg.lower() == '--ia32':
            arch = 'ia32'

    # write a message
    msg = '{} will be built for {} architecture.'.format(target, arch)
    print(msg)

    return arch


def build_apps(targets=None):
    if targets is None:
        targets = pymake.build_targets()
    else:
        if isinstance(targets, str):
            targets = [targets]

    for target in targets:

        # set double precision flag
        if target == 'swt_v4':
            double = True
        else:
            double = set_double(target)

        # set debug flag
        debug = set_debug(target)

        # set compiler
        fct, cct = set_compiler(target)

        # set architecture
        arch = set_arch(target)

        # set include_subdirs
        if target in ['mf6']:
            include_subdirs = True
        else:
            include_subdirs = False

        # set replace function
        replace_function = pymake.build_replace(target)

        # set download information
        if target in ['mt3dms']:
            modify_exe_name = False
            download_verify = False
            timeout = 10
        else:
            modify_exe_name = True
            download_verify = True
            timeout = 30

        # build the code
        pymake.build_program(target=target,
                             fc=fct,
                             cc=cct,
                             double=double,
                             debug=debug,
                             arch=arch,
                             include_subdirs=include_subdirs,
                             replace_function=replace_function,
                             modify_exe_name=modify_exe_name,
                             exe_dir=bindir,
                             download_dir='temp',
                             download_clean=True,
                             download_verify=download_verify,
                             timeout=timeout)

    return


if __name__ == '__main__':
    build_apps()
