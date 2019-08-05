import pytest
import random
from uatu.core.directed_graph import DirectedGraph

@pytest.fixture(scope='module')
def random_graph():
    graph_dict = {}
    for node in range(10):
        successors = set()
        for _ in range(random.randrange(0, 10)):
            successors.add(random.randrange(0, 10))
        graph_dict[node] = successors
    graph = DirectedGraph(graph_dict)
    return graph
