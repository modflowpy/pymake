from __future__ import print_function
import os
from .pymake import get_ordered_srcfiles
from .dag import get_f_nodelist
import pydotplus.graphviz as pydot


def to_pydot(dag, filename='mygraph.png'):

    # Create the graph
    graph = pydot.Dot(graph_type='digraph')

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

def add_pydot_nodes(graph, node_dict, n):
    if n in node_dict:
        return
    ttl = os.path.basename(n.name)
    pydotnode = pydot.Node(ttl, style="filled", fillcolor="red")
    node_dict[n] = pydotnode
    graph.add_node(pydotnode)
    if len(n.dependencies) > 0:
        for m in n.dependencies:
            add_pydot_nodes(graph, node_dict, m)
    return

def add_pydot_edges(graph, node_dict, edge_set, n):
    if len(n.dependencies) > 0:
        for m in n.dependencies:
            tpl = (n.name, m.name)
            if tpl not in edge_set:
                edge_set.add(tpl)
                edge = pydot.Edge(node_dict[n], node_dict[m])
                graph.add_edge(edge)
                add_pydot_edges(graph, node_dict, edge_set, m)
    return

def make_plots(srcdir, outdir):
    """
    Create plots of module dependencies

    """
    srcfiles = get_ordered_srcfiles(srcdir)
    nodelist = get_f_nodelist(srcfiles)
    for n in nodelist:
        print(os.path.basename(n.name))
        for m in n.dependencies:
            print('  ' + os.path.basename(m.name))
        print('')

    if not os.path.isdir(outdir):
        raise Exception('output directory does not exist')

    for n in nodelist:
        graph = pydot.Dot(graph_type='digraph')
        node_dict = {}
        add_pydot_nodes(graph, node_dict, n)
        edge_set = set()
        add_pydot_edges(graph, node_dict, edge_set, n)
        filename = os.path.join(outdir, os.path.basename(n.name) + '.png')
        print('Creating ' + filename)
        graph.write_png(filename)

    return

if __name__ == "__main__":

    srcdir = 'src'
    outdir = 'img'
    make_plots(srcdir, outdir)
