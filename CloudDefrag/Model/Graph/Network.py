import math
from abc import ABC
from typing import List

from CloudDefrag.Model.Graph.EnhancedGraph import EnhancedGraph
from CloudDefrag.Model.Graph.Link import Link, PhysicalLink, VirtualLink
from CloudDefrag.Model.Graph.Node import Node, Server, Router, VirtualMachine, DummyVirtualMachine
from CloudDefrag.Logging.Logger import Logger



class Network(EnhancedGraph, ABC):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._network_nodes = []
        self._network_edges = []
        if "network_nodes" in kwargs:
            for n in kwargs["network_nodes"]:
                self.add_network_node(n)
        if "network_edges" in kwargs:
            for e in kwargs["network_edges"]:
                self.add_network_edge(e)

    @property
    def network_nodes(self):
        return self._network_nodes

    @property
    def network_edges(self):
        return self._network_edges

    def get_links(self) -> List:
        links = []
        for source, target, attributes in self.edges(data=True):
            links.append(attributes['object'])
        return links

    def get_node_dict(self):
        return {v.node_name: v for v in self.network_nodes}

    def get_node_by_name(self, name):
        return self.get_node_dict()[name]

    def get_links_dict(self):
        node_dict = {}
        for link in self.get_links():
            node_dict[link.name] = link
        return node_dict

    def get_links_dict_full_with_reverse_names(self):
        node_dict = {}
        for link in self.get_links():
            node_dict[link.name] = link
            node_dict[link.reverse_name] = link
        return node_dict

    def get_link_by_name(self, name):
        return self.get_links_dict_full_with_reverse_names()[name]

    def add_network_node(self, node: Node, **kwargs):
        self._network_nodes.append(node)
        self.add_node(node, **kwargs)

    def add_network_edge(self, edge: Link, **kwargs):
        self._network_edges.append(edge)
        self.add_edge(edge.source, edge.target, object=edge, weight=edge.link_specs.propagation_delay)

    def get_link_between(self, n1: Node, n2: Node) -> Link:
        return self.get_edge_data(n1, n2)["object"]

    def get_link_by_name_between(self, n_str1: str, n_str2: str) -> VirtualLink:
        nodes_dict = self.get_node_dict()
        n1 = nodes_dict[n_str1]
        n2 = nodes_dict[n_str2]
        return self.vm_net.get_edge_data(n1, n2)["object"]


class PhysicalNetwork(Network):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Logger.log.info(f"Created physical network {self.name}")

    @property
    def compute_index(self):
        x = 0
        y = 0
        for server in self.get_servers():
            x += server.weight * server.node_score
            y += server.weight
        score = math.ceil(x / y)
        return score

    @property
    def communication_index(self):
        x = 0
        y = 0
        for link in self.get_links():
            x += link.weight * link.link_score
            y += link.weight
        score = math.ceil(x / y)
        return score

    def get_servers(self) -> List[Server]:
        servers = []
        for node in list(self.nodes):
            if isinstance(node, Server):
                servers.append(node)
        return servers

    def get_routers(self) -> List[Router]:
        routers = []
        for node in list(self.nodes):
            if isinstance(node, Router):
                routers.append(node)
        return routers

    def get_gateway_routers(self) -> List[Router]:
        routers = []
        for node in list(self.nodes):
            if isinstance(node, Router):
                if node.is_gateway:
                    routers.append(node)
        return routers




class VirtualNetwork(Network):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Logger.log.info(f"Created virtual network {self.name}")

    def get_vms(self) -> List[VirtualMachine]:
        vms = []
        for node in list(self.nodes):
            if isinstance(node, VirtualMachine):
                vms.append(node)
        return vms

    def get_vms_except_dummy(self) -> List[VirtualMachine]:
        vms = []
        for node in list(self.nodes):
            if isinstance(node, DummyVirtualMachine):
                continue
            else:
                vms.append(node)
        return vms

    def get_dummy_vm(self):
        dummy_vm = None
        for vm in self.get_vms():
            if isinstance(vm, DummyVirtualMachine):
                dummy_vm = vm
                return dummy_vm
        return dummy_vm

    def get_vms_dict(self):
        return {v.node_name: v for v in self.vms}

    def get_gateway_router(self) -> Router:
        router = None
        for node in self._network_nodes:
            if isinstance(node, DummyVirtualMachine):
                router = node.gateway_router
                return router
        return router
