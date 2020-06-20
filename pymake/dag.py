"""Set of classes for building a directed acyclic graph.

Can be used to determine the order of dependencies.  Can be used to
determine compiling order, for example.  Topological sort pseudocode
based on: http://en.wikipedia.org/wiki/Topological_sorting

"""

from __future__ import print_function

__author__ = "Christian D. Langevin"
__date__ = "March 20, 2014"
__version__ = "1.0.0"
__maintainer__ = "Christian D. Langevin"
__email__ = "langevin@usgs.gov"
__status__ = "Production"

import re
import os


class Node(object):
    def __init__(self, name):
        self.name = name
        self.dependencies = []
        return

    def add_dependency(self, d):
        """Add dependency if not already in list."""
        if d not in self.dependencies:
            self.dependencies.append(d)
        return


class DirectedAcyclicGraph(object):
    def __init__(self, nodelist):
        self.nodelist = nodelist
        return

    def toposort(self):
        """Perform topological sort."""
        sort_list = []  # empty list that will contain sorted elements

        # build a list of nodes with no dependencies
        tset = set([])
        for node in self.nodelist:
            if len(node.dependencies) == 0:
                tset.add(node)
        if len(tset) == 0:
            for node in self.nodelist:
                print(node.name, [nn.name for nn in node.dependencies])
            raise Exception('All nodes have dependencies')

        # build up the list
        while len(tset) > 0:
            node = tset.pop()
            sort_list.append(node)
            for mnode in self.nodelist:
                if node in mnode.dependencies:
                    mnode.dependencies.remove(node)
                    if len(mnode.dependencies) == 0:
                        tset.add(mnode)

        # check to make sure no remaining dependencies
        for node in sort_list:
            if len(node.dependencies) > 0:
                raise Exception('Graph has at least one cycle')

        return sort_list


def get_f_nodelist(srcfiles):
    # create a dictionary that has module name and source file name
    # create a dictionary that has a list of modules used within each source
    # create a list of Nodes for later ordering
    # create a dictionary of nodes
    module_dict = {}
    sourcefile_module_dict = {}
    nodelist = []
    nodedict = {}
    for srcfile in srcfiles:
        node = Node(srcfile)
        nodelist.append(node)
        nodedict[srcfile] = node
        try:
            f = open(srcfile, 'rb')
        except:
            print('get_f_nodelist: could not open {}'.format(
                os.path.basename(srcfile)))
            sourcefile_module_dict[srcfile] = []
            continue
        lines = f.read()
        lines = lines.decode('ascii', 'replace').splitlines()
        # develop a list of modules in the file
        modulelist = []  # list of modules used by this source file
        for idx, line in enumerate(lines):
            linelist = line.strip().split()
            if len(linelist) == 0:
                continue
            if linelist[0].upper() in ['MODULE', 'SUBMODULE']:
                modulename = linelist[1].upper()
                module_dict[modulename] = srcfile
            if linelist[0].upper() == 'USE':
                modulename = linelist[1].split(',')[0].upper()
                if modulename not in modulelist:
                    modulelist.append(modulename)
        # update the dictionary if any entries have been found
        sourcefile_module_dict[srcfile] = modulelist
        # close the src file
        f.close()

    # go through and add the dependencies to each node
    for node in nodelist:
        srcfile = node.name
        try:
            modulelist = sourcefile_module_dict[srcfile]
            for m in modulelist:
                if m in module_dict:
                    mlocation = module_dict[m]
                    if mlocation != srcfile:
                        # print 'adding dependency: ', srcfile, mlocation
                        node.add_dependency(nodedict[mlocation])
        except:
            print('get_f_nodelist: {} key does not exist'.format(srcfile))

    return nodelist


def get_dag(nodelist):
    """Create a dag from the nodelist."""
    dag = DirectedAcyclicGraph(nodelist)
    return dag


def order_source_files(srcfiles):
    """Use a dag and a nodelist to order the fortran source files."""
    nodelist = get_f_nodelist(srcfiles)
    dag = get_dag(nodelist)
    orderednodes = dag.toposort()
    osrcfiles = []
    for node in orderednodes:
        osrcfiles.append(node.name)
    return osrcfiles


def order_c_source_files(srcfiles):
    # create a dictionary that has module name and source file name
    # create a dictionary that has a list of modules used within each source
    # create a list of Nodes for later ordering
    # create a dictionary of nodes
    module_dict = {}
    sourcefile_module_dict = {}
    nodelist = []
    nodedict = {}
    for srcfile in srcfiles:
        node = Node(srcfile)
        nodelist.append(node)
        nodedict[srcfile] = node
        try:
            f = open(srcfile, 'rb')
        except:
            print('order_c_source_files: could not open {}'.format(
                os.path.basename(srcfile)))
            sourcefile_module_dict[srcfile] = []
            continue
        lines = f.read()
        lines = lines.decode('ascii', 'replace').splitlines()
        # develop a list of modules in the file
        modulelist = []  # list of modules used by this source file
        for idx, line in enumerate(lines):
            linelist = line.strip().split()
            if len(linelist) == 0:
                continue
            if linelist[0].upper() == '#INCLUDE':
                modulename = linelist[1].upper()
                for cval in ['"', "'", '<', '>']:
                    modulename = modulename.replace(cval, '')
                # add source file for this c(pp) file if it is the same
                # as the include file without the extension
                bn = os.path.basename(srcfile)
                if os.path.splitext(modulename)[0] == \
                        os.path.splitext(bn)[0].upper():
                    module_dict[modulename] = srcfile
                # add include file name
                if modulename not in modulelist:
                    modulelist.append(modulename)
        # update the dictionary if any entries have been found
        sourcefile_module_dict[srcfile] = modulelist
        # close the src file
        f.close()

    # go through and add the dependencies to each node
    for node in nodelist:
        srcfile = node.name
        try:
            modulelist = sourcefile_module_dict[srcfile]
            for m in modulelist:
                if m in module_dict:
                    mlocation = module_dict[m]
                    if mlocation != srcfile:
                        # print 'adding dependency: ', srcfile, mlocation
                        node.add_dependency(nodedict[mlocation])
        except:
            print(
                'order_c_source_files: {} key does not exist'.format(srcfile))

    dag = get_dag(nodelist)
    orderednodes = dag.toposort()
    osrcfiles = []
    for node in orderednodes:
        osrcfiles.append(node.name)
    return osrcfiles


if __name__ == '__main__':
    a = Node('a')
    b = Node('b')
    c = Node('c')
    d = Node('d')

    a.add_dependency(b)
    a.add_dependency(c)
    c.add_dependency(d)
    d.add_dependency(b)

    nodelist = [a, b, c, d]

    dag = DirectedAcyclicGraph(nodelist)
    ordered = dag.toposort()
    print('length of output: ', len(ordered))

    for n in ordered:
        print(n.name)
