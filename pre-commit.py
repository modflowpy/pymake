#!/usr/bin/python

from __future__ import print_function
import subprocess
import os
import sys
import datetime

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
                '{}'.format(v1), 
                '{}'.format(0))
    tag = '.'.join(tag_type)
     

def update_version():
    try:
        pth = os.path.join(pak, 'version.py')
        
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
            vmicro = vmicro + 1
    
        v1, b1 = get_version_str(vmajor, vminor, vmicro, vcommit)
    
        print('Updating version:')
        print('  ', v0, '->', v1)
        print('Updating build:')
        print('  ', b0, '->', b1)
    
        # write new version file
        f = open(pth, 'w')
        f.write('#{} version file automatically '.format(pak) +
                'created using...{0}\n'.format(os.path.basename(__file__)))
        f.write('#            created on......' +
                '{0}\n'.format(datetime.datetime.now().strftime("%B %d, %Y %H:%M:%S")))
        f.write('\n')
        f.write('major = {}\n'.format(vmajor))
        f.write('minor = {}\n'.format(vminor))
        f.write('micro = {}\n'.format(vmicro))
        f.write('commit = {}\n\n'.format(vcommit))
        f.write("__version__='{}'\n".format(v1))
        f.write("__build__='{}'\n".format(b1))
        f.close()
        print('Succesfully updated version.py')
    except:
        print('There was a problem updating the version file')
        sys.exit(1)

def add_updated_version():
    try:
        opth = os.getcwd() 
        print('In: {}'.format(opth))
        #npth = os.path.join('..', '..')
        #print('Changing to: {}'.format(os.path.abspath(npth)))
        #os.chdir(npth)
        # add modified version file
        print('Adding updated version file to repo')
        b = subprocess.Popen(("git", "add", "{}/version.py".format(pak)),
                             stdout=subprocess.PIPE).communicate()[0]
        #print('Changing back to: {}'.format(opth))
        #os.chdir(opth)
        
    except:
        print('Could not add updated version file')
        sys.exit(1) 

if __name__ == "__main__":
    update_version()
    add_updated_version()
    
