"""Set of classes for building a directed acyclic graph (DAG). A DAG can be
used to determine the order of dependencies in source code and determine
compiling order.  Topological sort pseudocode based on:
https://en.wikipedia.org/wiki/Topological_sorting
"""
__author__ = "Christian D. Langevin"
__date__ = "March 20, 2014"
__version__ = "1.0.0"
__maintainer__ = "Christian D. Langevin"
__email__ = "langevin@usgs.gov"
__status__ = "Production"

import os


class Node(object):
    def __init__(self, name):
        self.name = name
        self.dependencies = []
        return

    def add_dependency(self, dependency):
        """Add dependency if not already in list."""
        if dependency not in self.dependencies:
            self.dependencies.append(dependency)
        return


class DirectedAcyclicGraph(object):
    def __init__(self, nodelist, networkx=False):
        self.nodelist = nodelist
        self.networkx = networkx
        return

    def toposort(self):
        """Perform topological sort."""
        sort_list = []  # empty list that will contain sorted elements

        # use the NetworkX python package to generate the DAG
        if self.networkx:
            try:
                import networkx as nx
            except ModuleNotFoundError:
                raise ModuleNotFoundError(
                    "install networkx using `pip install networkx"
                )

            # create a simple dictionary with the node as the key and
            # the dependencies for each node
            node_dict = {}
            for node in self.nodelist:
                node_dict[node.name] = node.dependencies

            # build the graph
            ts = nx.DiGraph()
            for node in self.nodelist:
                ts.add_node(node.name)
                if len(node.dependencies) > 0:
                    for nn in node.dependencies:
                        ts.add_edge(node.name, nn.name)

            # generate the DAG
            order = tuple(nx.topological_sort(ts))[::-1]

            # build sort_list from the DAG and add dependencies from node_dict
            for name in order:
                node = Node(name)
                for dependency in node_dict[name]:
                    node.add_dependency(dependency)
                sort_list.append(node)
        # use the original pymake DAG algorithm
        else:
            # build a list of nodes with no dependencies
            tset = set([])
            for node in self.nodelist:
                if len(node.dependencies) == 0:
                    tset.add(node)
            if len(tset) == 0:
                for node in self.nodelist:
                    print(node.name, [nn.name for nn in node.dependencies])
                raise Exception("All nodes have dependencies")

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
                    raise Exception("Graph has at least one cycle")

        return sort_list


def _get_f_nodelist(srcfiles):
    """Get fortran DAG nodelist.

    Parameters
    ----------
    srcfiles : list
        list of source file paths

    Returns
    -------
    nodelist : list
        list of DAG nodes

    """
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
            f = open(srcfile, "rb")
        except:
            print(
                "get_f_nodelist: could not open {}".format(
                    os.path.basename(srcfile)
                )
            )
            sourcefile_module_dict[srcfile] = []
            continue
        lines = f.read()
        lines = lines.decode("ascii", "replace").splitlines()

        # develop a list of modules in the file
        modulelist = []  # list of modules used by this source file
        for idx, line in enumerate(lines):
            linelist = line.strip().split()
            if len(linelist) == 0:
                continue
            if linelist[0].upper() in ["MODULE", "SUBMODULE"]:
                modulename = linelist[1].upper()
                module_dict[modulename] = srcfile
            if linelist[0].upper() == "USE":
                modulename = linelist[1].split(",")[0].upper()
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
            modulelist = sorted(sourcefile_module_dict[srcfile])
            for m in modulelist:
                if m in module_dict:
                    mlocation = module_dict[m]
                    if mlocation != srcfile:
                        # print 'adding dependency: ', srcfile, mlocation
                        node.add_dependency(nodedict[mlocation])
        except:
            print("get_f_nodelist: {} key does not exist".format(srcfile))

    return nodelist


def _get_dag(nodelist, networkx):
    """Create a DAG from the nodelist.

    Parameters
    ----------
    nodelist : list
        list of DAG nodes
    networkx : bool
        boolean indicating if the NetworkX python package should be used
        to determine the DAG.

    Returns
    -------
    dag : DirectedAcyclicGraph
        DAG object

    """
    dag = DirectedAcyclicGraph(nodelist, networkx=networkx)
    return dag


def _order_f_source_files(srcfiles, networkx):
    """Use a dag and a nodelist to order the fortran source files.

    Parameters
    ----------
    srcfiles : list
        list of source file paths
    networkx : bool
        boolean indicating if the NetworkX python package should be used
        to determine the DAG.

    Returns
    -------
    osrcfiles : list
        DAG ordered list of source files

    """
    nodelist = _get_f_nodelist(srcfiles)
    dag = _get_dag(nodelist, networkx=networkx)
    orderednodes = dag.toposort()
    osrcfiles = []
    for node in orderednodes:
        osrcfiles.append(node.name)

    return osrcfiles


def _order_c_source_files(srcfiles, networkx):
    """Create a ordered list of c/c++ source files.

    Parameters
    ----------
    srcfiles : list
        list of source file paths
    networkx : bool
        boolean indicating if the NetworkX python package should be used
        to determine the DAG.

    Returns
    -------
    osrcfiles : list
        DAG ordered list of c/c++ source files

    """
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
            f = open(srcfile, "rb")
        except:
            print(
                "order_c_source_files: could not open {}".format(
                    os.path.basename(srcfile)
                )
            )
            sourcefile_module_dict[srcfile] = []
            continue
        lines = f.read()
        lines = lines.decode("ascii", "replace").splitlines()

        # develop a list of modules in the file
        modulelist = []  # list of modules used by this source file
        for idx, line in enumerate(lines):
            linelist = line.strip().split()
            if len(linelist) == 0:
                continue
            if linelist[0].upper() == "#INCLUDE":
                modulename = linelist[1].upper()
                for cval in ['"', "'", "<", ">"]:
                    modulename = modulename.replace(cval, "")

                # add source file for this c(pp) file if it is the same
                # as the include file without the extension
                bn = os.path.basename(srcfile)
                if (
                    os.path.splitext(modulename)[0]
                    == os.path.splitext(bn)[0].upper()
                ):
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
            msg = "order_c_source_files: " + "{} key does not exist".format(
                srcfile
            )
            print(msg)

    dag = _get_dag(nodelist, networkx=networkx)
    orderednodes = dag.toposort()
    osrcfiles = []
    for node in orderednodes:
        osrcfiles.append(node.name)

    return osrcfiles


if __name__ == "__main__":
    a = Node("a")
    b = Node("b")
    c = Node("c")
    d = Node("d")

    a.add_dependency(b)
    a.add_dependency(c)
    c.add_dependency(d)
    d.add_dependency(b)

    nodelist = [a, b, c, d]

    dag = DirectedAcyclicGraph(nodelist)
    ordered = dag.toposort()
    print("length of output: ", len(ordered))

    for n in ordered:
        print(n.name)
