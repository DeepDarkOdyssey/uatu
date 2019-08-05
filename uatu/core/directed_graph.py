from typing import Optional, Iterable, Dict, Set, DefaultDict, List
from collections import defaultdict
from copy import copy


class DirectedGraph(object):
    def __init__(self, graph_dict: Optional[Dict[str, Set[str]]] = None):
        self._graph = dict()
        for node, successors in graph_dict.items():
            if node not in self:
                self.add_node(node)
            for successor in successors:
                self.add_arc(node, successor, True)

    def add_node(self, node: str):
        if node in self:
            raise KeyError(f"Record {node} already exists in graph")
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

    def add_arc(self, start: str, end: str, create_nodes=False):
        if create_nodes:
            if start not in self:
                self.add_node(start)
            if end not in self:
                self.add_node(end)
        else:
            if start not in self or end not in self:
                raise KeyError("Specified nodes don't exists in graph")
        self._graph[start].add(end)

    def delete_arc(self, start: str, end: str):
        if start not in self or end not in self:
            raise KeyError("Specified nodes don't exists in graph")
        if end not in self._graph[start]:
            raise KeyError(f"There is no arc between {start} and {end}")
        self._graph[start].remove(end)

    def delete_arcs(self, start: str, end: str):
        possible_paths = self.find_path(start, end)
        for path in possible_paths:
            for i in range(len(path) - 1):
                self.delete_arc(path[i], path[i + 1])

    def find_path_util(
        self,
        node: str,
        end: str,
        visited: DefaultDict,
        path: List[str],
        paths: List[List[str]],
    ):
        visited[node] = True
        path.append(node)
        if node == end:
            paths.append(copy(path))
        else:
            for successor in self._graph[node]:
                if visited[successor] == False:
                    self.find_path_util(successor, end, visited, path, paths)
        path.pop()
        visited[node] = False

    def find_path(self, start: str, end: str):
        visited = defaultdict(lambda: False)
        path, paths = [], []
        self.find_path_util(start, end, visited, path, paths)
        return paths

    def __contains__(self, node: str):
        return node in self._graph

    def __getitem__(self, node):
        if not node in self:
            raise KeyError(f"Record {node} does not exists in graph")
        successors = self._graph[node]
        predecessors = set()
        for key, values in self._graph.items():
            if node in values:
                predecessors.add(key)
        return {"predecessors": predecessors, "successors": successors}

    def __len__(self):
        return len(self._graph)
