"""Dependency graphs for applications can be created using:

.. code-block:: python

    import os
    import pymake

    srcpth = os.path.join("..", "src")
    deppth = "dependencies"
    if not os.path.exists(deppth):
        os.makedirs(deppth)

    pymake.visualize.make_plots(srcpth, deppth, include_subdir=True)



"""
import os

from ..utils._compiler_language_files import (
    _get_srcfiles,
    _get_ordered_srcfiles,
)
from ..utils._dag import _get_f_nodelist

try:
    import pydotplus.graphviz as pydot
except:
    pydot = None


def to_pydot(dag, filename="mygraph.png"):
    """Create a png file of a Directed Acyclic Graph

    Parameters
    ----------
    dag : object
        directed acyclic graph
    filename : str
        path of the graph png

    Returns
    -------

    """
    # evaluate if pydot plus is installed
    if pydot is None:
        msg = "pydotplus must be installed to use " + "{}".format(
            make_plots.__module__ + "." + make_plots.__name__
        )
        raise ModuleNotFoundError(msg)

    # Create the graph
    graph = pydot.Dot(graph_type="digraph")

    # Add the nodes
    node_dict = {}
    for n in dag.nodelist:
        pydotnode = pydot.Node(n.name, style="filled", fillcolor="red")
        node_dict[n] = pydotnode
        graph.add_node(pydotnode)

    # Add the edges
    for n in dag.nodelist:
        for m in n.dependencies:
            graph.add_edge(pydot.Edge(node_dict[n], node_dict[m]))

    graph.write_png(filename)
    return


def _add_pydot_nodes(graph, node_dict, n, ilev, level):
    """

    Parameters
    ----------
    graph
    node_dict
    n
    ilev
    level

    Returns
    -------

    """
    if ilev == level:
        return

    if n in node_dict:
        return

    ttl = os.path.basename(n.name)
    pydotnode = pydot.Node(ttl, style="filled", fillcolor="red", label=ttl)
    node_dict[n] = pydotnode
    graph.add_node(pydotnode)
    if len(n.dependencies) > 0:
        for m in n.dependencies:
            _add_pydot_nodes(graph, node_dict, m, ilev + 1, level)
    return


def _add_pydot_edges(graph, node_dict, edge_set, n, ilev, level):
    """

    Parameters
    ----------
    graph
    node_dict
    edge_set
    n
    ilev
    level

    Returns
    -------

    """
    if ilev == level:
        return

    if len(n.dependencies) > 0:
        for m in n.dependencies:
            if m not in node_dict:
                continue
            tpl = (n.name, m.name)
            if tpl not in edge_set:
                edge_set.add(tpl)
                edge = pydot.Edge(node_dict[n], node_dict[m])
                graph.add_edge(edge)
                _add_pydot_edges(
                    graph, node_dict, edge_set, m, ilev + 1, level
                )
    return


def make_plots(
    srcdir,
    outdir,
    include_subdir=False,
    level=3,
    extension=".png",
    verbose=False,
    networkx=False,
):
    """Create plots of module dependencies.

    Parameters
    ----------
    srcdir : str
        path for source files
    outdir : str
        path for output images
    include_subdir : bool
        boolean indicating is subdirectories in the source file directory
        should be included
    level : int
        dependency level (1 is the minimum)
    extension : str
        output extension (default is .png)
    verbose : bool
        boolean indicating if output will be printed to the terminal
    networkx : bool
        boolean indicating that the NetworkX python package will be used to
        create the Directed Acyclic Graph (DAG) used to determine the order
        source files are compiled in. The NetworkX package tends to result in
        a unique DAG more often than the standard algorithm used in pymake.
        (default is False)

    Returns
    -------

    """
    # evaluate if pydot plus is installed
    if pydot is None:
        msg = "pydotplus must be installed to use " + "{}".format(
            make_plots.__module__ + "." + make_plots.__name__
        )
        raise ModuleNotFoundError(msg)

    srcfiles = _get_ordered_srcfiles(
        _get_srcfiles(srcdir, include_subdir), networkx=networkx
    )
    nodelist = _get_f_nodelist(srcfiles)
    for idx, n in enumerate(nodelist):
        if verbose:
            print("{:<3d}: {}".format(idx + 1, os.path.basename(n.name)))
            for jdx, m in enumerate(n.dependencies):
                msg = "     {:<3d}: {}".format(
                    jdx + 1, os.path.basename(m.name)
                )
                print(msg)

    if not os.path.isdir(outdir):
        raise Exception("output directory does not exist")

    for n in nodelist:
        filename = os.path.join(outdir, os.path.basename(n.name) + extension)
        if verbose:
            print("Creating " + filename)
        graph = pydot.Dot(graph_type="digraph")
        node_dict = {}
        ilev = 0
        _add_pydot_nodes(graph, node_dict, n, ilev, level)
        edge_set = set()
        ilev = 1
        _add_pydot_edges(graph, node_dict, edge_set, n, ilev, level)
        if extension == ".png":
            graph.write_png(filename)
        elif extension == ".pdf":
            graph.write_pdf(filename)
        elif extension == ".dot":
            graph.write_dot(filename)
        else:
            raise Exception("unknown file extension: {}".format(extension))

    return


if __name__ == "__main__":
    srcdir = "src"
    outdir = "img"
    make_plots(srcdir, outdir)
