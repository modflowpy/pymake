"""

Set of classes for building a directed acyclic graph.  Can be used to
determine the order of dependencies.  Can be used to determine compiling
order, for example.  Topological sort pseudocode based on:
http://en.wikipedia.org/wiki/Topological_sorting

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
import codecs


class Node(object):
    def __init__(self, name):
        self.name = name
        self.dependencies = []
        return

    def add_dependency(self, d):
        """
        Add dependency if not already in list
        """
        if d not in self.dependencies:
            self.dependencies.append(d)
        return


class DirectedAcyclicGraph(object):
    def __init__(self, nodelist):
        self.nodelist = nodelist
        return

    def toposort(self):
        """
        Perform topological sort
        """
        l = []  # empty list that will contain sorted elements

        # build a list of nodes with no dependencies
        s = set([])
        for n in self.nodelist:
            if len(n.dependencies) == 0:
                s.add(n)
        if len(s) == 0:
            for n in self.nodelist:
                print(n.name, [nn.name for nn in n.dependencies])
            raise Exception('All nodes have dependencies')

        # build up the list
        while len(s) > 0:
            n = s.pop()
            l.append(n)
            for m in self.nodelist:
                if n in m.dependencies:
                    m.dependencies.remove(n)
                    if len(m.dependencies) == 0:
                        s.add(m)

        # check to make sure no remaining dependencies
        for n in l:
            if len(n.dependencies) > 0:
                raise Exception('Graph has at least one cycle')

        return l


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
        # in python 3 this could just be f = open(srcfile, 'r', encoding='ascii', errors='replace')
        f = codecs.open(srcfile, 'r', encoding='ascii', errors='replace')
        try:
            modulelist = []  # list of modules used by this source file
            for idx, line in enumerate(f):
                linelist = line.strip().split()
                if len(linelist) == 0:
                    continue
                if linelist[0].upper() == 'MODULE':
                    modulename = linelist[1].upper()
                    module_dict[modulename] = srcfile
                if linelist[0].upper() == 'USE':
                    modulename = linelist[1].split(',')[0].upper()
                    if modulename not in modulelist:
                        modulelist.append(modulename)
            sourcefile_module_dict[srcfile] = modulelist
            f.close()
        except:
            print('get_f_nodelist: {} - could not decode data on line {}'.format(os.path.basename(srcfile), idx+1))

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
    """
    Create a dag from the nodelist
    """
    dag = DirectedAcyclicGraph(nodelist)
    return dag


def order_source_files(srcfiles):
    """
    Use a dag and a nodelist to order the fortran source files
    """
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
    for srcfile in srcfiles:  # contains only .c or .cpp
        node = Node(srcfile.lower())
        nodelist.append(node)
        nodedict[srcfile.lower()] = node

        # search .c or .cpp file
        f = open(srcfile, 'r')
        modulelist = []  # list of modules used by this source file
        module_dict[os.path.basename(srcfile).lower()] = srcfile.lower()

        for line in f:
            linelist = line.strip().split()
            if len(linelist) == 0:
                continue
            if linelist[0] == '#include':
                m = re.match('"([^\.]*).h(pp|)"', linelist[1])
                if m:
                    modulename = m.group(1) + '.' + 'c' + m.group(2)
                    if modulename not in modulelist:
                        modulelist.append(modulename)
        f.close()

        # search corresponding .h or .hpp file
        m = re.match('(.*).c(pp|)', srcfile.lower())
        if m and os.path.isfile(m.group(1) + '.' + 'h' + m.group(2)):
            f = open(m.group(1) + '.' + 'h' + m.group(2), 'r')
            # modulelist = []  #list of modules used by this source file
            # module_dict[srcfile] = srcfile
            for line in f:
                linelist = line.strip().split()
                if len(linelist) == 0:
                    continue
                if linelist[0] == '#include':
                    m = re.match('"([^\.]*).h(pp|)"', linelist[1])
                    if m:
                        modulename = m.group(1) + '.' + 'c' + m.group(2)
                        if modulename not in modulelist:
                            modulelist.append(modulename)
            # sourcefile_module_dict[srcfile] = modulelist
            f.close()
        else:
            print("no corresponding header file found for ", srcfile)

        sourcefile_module_dict[srcfile.lower()] = modulelist

    # go through and add the dependencies to each node
    for node in nodelist:
        srcfile = node.name.lower()
        modulelist = sourcefile_module_dict[srcfile]
        for m in modulelist:
            mlocation = module_dict[m]
            if mlocation != srcfile:
                # print 'adding dependency: ', srcfile, mlocation
                node.add_dependency(nodedict[mlocation])

    # build the ordered dependency list using the topological sort method
    if len(nodelist) > 0:
        orderednodes = DirectedAcyclicGraph(nodelist).toposort()
    else:
        orderednodes = []
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
