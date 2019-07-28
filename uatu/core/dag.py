from typing import Optional, Iterable, Dict, Set


class DAG(object):
    def __init__(self, graph_dict: Optional[Dict[str, Set[str]]] = None):
        self._graph = dict()
        for node, successors in graph_dict.items():
            self.add_node(node)
            for successor in successors:
                self.add_arc(node, successor)

    def add_node(self, node: str):
        if node in self:
            raise KeyError(f'Node {node} already exists in graph')
        else:
            self._graph[node] = set()
    
    def add_nodes(self, nodes: Iterable[str]):
        for node in nodes:
            self.add_node(node)
    
    def delete_node(self, node: str):
        self._graph.pop(node)
        for values in self._graph.values():
            values.discard(node)

    def delete_nodes(self, nodes: Iterable[str]):
        for node in nodes:
            self.delete_nodes(node)

    def add_arc(self, begin: str, end: str, create_nodes=False):
        if create_nodes:
            if begin not in self:
                self.add_node(begin)
            if end not in self:
                self.add_node(end)
        else:
            if begin not in self or end not in self:
                raise KeyError("Specified nodes don't exists in graph")
            self._graph[begin] = end

    def delete_arc(self, begin: str, end: str):
        if begin not in self or end not in self:
            raise KeyError("Specified nodes don't exists in graph")
        if end not in self._graph[begin]:
            raise KeyError(f'There is no arc between {begin} and {end}')
        self._graph[begin].remove(end)

    def delete_arcs(self, begin: str, end: str):
        pass

    def __contains__(self, node: str):
        return node in self._graph

    def __getattribute__(self, node):
        if node not in self:
            raise KeyError(f"Node {node} does not exists in graph")
        successors = self._graph[node]
        predecessors = set()
        for key, values in self._graph.items():
            if node in values:
                predecessors.add(key)
        return {'predecessors': predecessors, 'successors': successors}

    def __len__(self):
        return len(self._graph)
