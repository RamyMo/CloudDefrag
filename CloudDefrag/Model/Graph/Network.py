from typing import List

from CloudDefrag.Model.Graph.EnhancedGraph import EnhancedGraph
from CloudDefrag.Model.Graph.Link import Link, PhysicalLink
from CloudDefrag.Model.Graph.Node import Node, Server, Router
from CloudDefrag.Logging.Logger import Logger


class Network(EnhancedGraph):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._network_nodes = kwargs["network_nodes"] if "network_nodes" in kwargs else []
        self._network_edges = kwargs["network_edges"] if "network_edges" in kwargs else []
        Logger.log.info(f"Created network {self.name}")

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

    @property
    def servers(self) -> List[Server]:
        servers = []
        for node in list(self.nodes):
            if isinstance(node, Server):
                servers.append(node)
        return servers

    @property
    def routers(self) -> List[Router]:
        routers = []
        for node in list(self.nodes):
            if isinstance(node, Router):
                routers.append(node)
        return routers

    @property
    def gateway_routers(self) -> List[Router]:
        routers = []
        for node in list(self.nodes):
            if isinstance(node, Router):
                if node.is_gateway:
                    routers.append(node)
        return routers

    @property
    def links(self) -> List[PhysicalLink]:
        links = []
        for source, target, attributes in self.edges(data=True):
            links.append(attributes['object'])
        return links
