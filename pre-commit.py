#!/usr/bin/python

from __future__ import print_function
import subprocess
import os
import sys
import datetime

files = ['version.py', 'README.md']
pak = 'pymake'


def get_version_str(v0, v1, v2, v3):
    version_type = ('{}'.format(v0),
                    '{}'.format(v1),
                    '{}'.format(v2))
    version = '.'.join(version_type)
    build_type = ('{}'.format(v0),
                  '{}'.format(v1),
                  '{}'.format(v2),
                  '{}'.format(v3))
    build = '.'.join(build_type)
    return version, build


def get_tag(v0, v1):
    tag_type = ('{}'.format(v0),
                '{}'.format(v1))
    tag = '.'.join(tag_type)
    return tag


def update_version():
    try:
        pth = os.path.join(pak, files[0])

        vmajor = 0
        vminor = 0
        vmicro = 0
        vcommit = 0
        lines = [line.rstrip('\n') for line in open(pth, 'r')]
        for line in lines:
            t = line.split()
            if 'major =' in line:
                vmajor = int(t[2])
            elif 'minor =' in line:
                vminor = int(t[2])
            elif 'micro =' in line:
                vmicro = int(t[2])
            elif 'commit =' in line:
                vcommit = int(t[2])

        v0, b0 = get_version_str(vmajor, vminor, vmicro, vcommit)

        # get current build number
        b = subprocess.Popen(("git", "describe", "--match", "build"),
                             stdout=subprocess.PIPE).communicate()[0]
        vcommit = int(b.decode().strip().split('-')[1]) + 2

        tag = get_tag(vmajor, vminor)
        print('determining version micro from {}'.format(tag))
        try:
            b = subprocess.Popen(("git", "describe", "--match", tag),
                                 stdout=subprocess.PIPE).communicate()[0]
            vmicro = int(b.decode().strip().split('-')[1]) + 1
        except:
            vmicro = 0

        v1, b1 = get_version_str(vmajor, vminor, vmicro, vcommit)

        print('Updating version:')
        print('  ', v0, '->', v1)
        print('Updating build:')
        print('  ', b0, '->', b1)

        # write new version file
        f = open(pth, 'w')
        f.write('# {} version file automatically '.format(pak) +
                'created using...{0}\n'.format(os.path.basename(__file__)))
        f.write('# created on...' +
                '{0}\n'.format(
                    datetime.datetime.now().strftime("%B %d, %Y %H:%M:%S")))
        f.write('\n')
        f.write('major = {}\n'.format(vmajor))
        f.write('minor = {}\n'.format(vminor))
        f.write('micro = {}\n'.format(vmicro))
        f.write('commit = {}\n\n'.format(vcommit))
        f.write("__version__ = '{:d}.{:d}'.format(major, minor)\n")
        f.write("__build__ = '{:d}.{:d}.{:d}'.format(major, minor, micro)\n")
        f.write("__git_commit__ = '{:d}'.format(commit)\n")
        f.close()
        print('Succesfully updated {}'.format(files[0]))
    except:
        print('There was a problem updating the version file')
        sys.exit(1)

    # update README.md with new version information
    update_readme_markdown(vmajor, vminor, vmicro)


def add_updated_files():
    try:
        # add modified version file
        print('Adding updated files to repo')
        b = subprocess.Popen(("git", "add", "-u"),
                             stdout=subprocess.PIPE).communicate()[0]
    except:
        print('Could not add updated files')
        sys.exit(1)


def update_readme_markdown(vmajor, vminor, vmicro):
    try:
        # determine current branch
        b = subprocess.Popen(("git", "status"),
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT).communicate()[0]
        if isinstance(b, bytes):
            b = b.decode('utf-8')

        # determine current buildstat branch
        for line in b.splitlines():
            if 'On branch' in line:
                branch = line.replace('On branch ', '').rstrip()
    except:
        print('Cannot update README.md - could not determine current branch')
        return

    # create version
    version = get_tag(vmajor, vminor)

    # read README.md into memory
    with open(files[1], 'r') as file:
        lines = [line.strip() for line in file]

    # rewrite README.md
    f = open(files[1], 'w')
    for line in lines:
        if '### Version ' in line:
            line = '### Version {}'.format(version)
            if branch != 'master':
                line += ' {} &mdash; build {}'.format(branch, vmicro)
        elif '[Build Status]' in line:
            line = '[![Build Status](https://travis-ci.org/modflowpy/' + \
                   'pymake.svg?branch={})]'.format(branch) + \
                   '(https://travis-ci.org/modflowpy/pymake)'
        elif '[Coverage Status]' in line:
            line = '[![Coverage Status](https://coveralls.io/repos/github/' + \
                   'modflowpy/pymake/badge.svg?branch={})]'.format(branch) + \
                   '(https://coveralls.io/github/modflowpy/' + \
                   'pymake?branch={})'.format(branch)
        f.write('{}\n'.format(line))
    f.close()

    return


if __name__ == "__main__":
    update_version()
    add_updated_files()
