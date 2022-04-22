from CloudDefrag.Model.Graph.EnhancedGraph import EnhancedGraph
from CloudDefrag.Model.Graph.Link import Link
from CloudDefrag.Model.Graph.Node import Node


class Network(EnhancedGraph):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._network_nodes = kwargs["network_nodes"] if "network_nodes" in kwargs else []
        self._network_edges = kwargs["network_edges"] if "network_edges" in kwargs else []

    @property
    def network_nodes(self):
        return self._network_nodes

    @property
    def network_edges(self):
        return self._network_edges

    def add_network_node(self, node: Node, **kwargs):
        self._network_nodes.append(node)
        self.add_node(node, **kwargs)

    def add_network_edge(self, edge: Link, **kwargs):
        self._network_edges.append(edge)
        self.add_edge(edge.source, edge.target, object=edge)
