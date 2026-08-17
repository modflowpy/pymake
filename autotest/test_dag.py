"""Tests for the graph that orders the source files.

Cases:
  - test_toposort_order       : a node is ordered before the nodes that depend
                                on it.
  - test_toposort_is_stable   : the same graph is ordered the same way whatever
                                order the nodes are given in, so a makefile
                                pymake writes can be reproduced.
"""

import random

import pytest

from pymake.utils._dag import DirectedAcyclicGraph, Node

# a base module several modules depend on and nothing depends on each other,
# so there is more than one order the nodes can be put in and an order that
# depends on the order the nodes were given in can be told apart from one that
# does not
_NAMES = ["base"] + [f"mod{idx}" for idx in range(8)]


def _graph(order):
    """Build a graph where every module depends on base and nothing else."""
    nodes = {name: Node(name) for name in _NAMES}
    for name in _NAMES:
        if name != "base":
            nodes[name].add_dependency(nodes["base"])
    return [nodes[name] for name in order]


@pytest.mark.base
def test_toposort_order() -> None:
    """A node is ordered before the nodes that depend on it."""
    order = [node.name for node in DirectedAcyclicGraph(_graph(_NAMES)).toposort()]

    assert order[0] == "base", f"base is not compiled first: {order}"
    assert sorted(order) == sorted(_NAMES), f"a node was lost or added: {order}"


@pytest.mark.base
def test_toposort_is_stable() -> None:
    """The order does not depend on the order the nodes are given in.

    The source files are found by walking a directory, which is read in the
    order the file system returns, so the order the nodes are given in differs
    from one operating system to another.
    """
    orders = set()
    names = list(_NAMES)
    for _ in range(8):
        random.shuffle(names)
        orders.add(
            tuple(node.name for node in DirectedAcyclicGraph(_graph(names)).toposort())
        )

    assert len(orders) == 1, f"the graph was ordered {len(orders)} different ways"
