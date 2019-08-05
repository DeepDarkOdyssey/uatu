from uatu.core.directed_graph import DirectedGraph
from .utils import random_graph


def test_initialize(random_graph: DirectedGraph):
    print()
    print(random_graph._graph)

def test_find_path(random_graph: DirectedGraph):
    print()
    print(random_graph.find_path(0, 9))
