import networkx as nx
import matplotlib.pyplot as plt
import pyvis
from IPython.core.display import HTML
from IPython.core.display_functions import display

from CloudDefrag.Model.Graph.Network import PhysicalNetwork, VirtualNetwork
from CloudDefrag.Model.Graph.Node import Server, Router


class NetworkVisualizer:

    def __init__(self, net: PhysicalNetwork) -> None:
        self._net = net
        self._pos = nx.spring_layout(self._net, seed=3113794652)  # positions for all nodes
        self._colors = nx.get_node_attributes(net, 'color').values()
        self._options = {
            'node_size': 500,
            'width': 1,
            'node_color': self._colors,
            'pos': self._pos,
            'with_labels': True,
            'width': 2,
            "edgecolors": "tab:gray"
        }

    def plot(self):
        nx.draw(self._net, **self._options)
        net_name = self._net.name
        plt.savefig(f"output/{net_name}.png")

    def interactive_visual(self):
        # create vis network
        vis_net = pyvis.network.Network(notebook=True)
        # vis_net.from_nx(self._net)
        from_nx_to_pyvis(vis_net, nx_graph=self._net)
        vis_net.show("output/Visualization/net.html")


class RequestVisualizer:
    # TODO: Fix RequestVisualizer
    def __init__(self, net: VirtualNetwork) -> None:
        self._net = net
        self._pos = nx.spring_layout(self._net, seed=3113794652)  # positions for all nodes
        # self._colors = nx.get_node_attributes(net, 'color').values()
        self._options = {
            'node_size': 500,
            'width': 1,
            # 'node_color': self._colors,
            'pos': self._pos,
            'with_labels': True,
            'width': 2,
            "edgecolors": "tab:gray"
        }

    def plot(self):
        nx.draw(self._net, **self._options)
        net_name = self._net.name
        plt.savefig(f"output/{net_name}.png")


def from_nx_to_pyvis(pyvis_net, nx_graph, default_node_size=20, default_edge_weight=2):
    assert (isinstance(nx_graph, nx.Graph))
    edges = nx_graph.edges(data=True)
    nodes = nx_graph.nodes(data=True)
    default_node_options = {"size": default_node_size, "shape": "circle"}
    default_edge_options = {"width": default_edge_weight, "color": "black"}
    if len(edges) > 0:
        for e in edges:
            # Get Node options for pyvis from nx node
            node1_options = get_node_options(nodes[e[0]], e[0], default_node_options)
            node2_options = get_node_options(nodes[e[1]], e[1], default_node_options)
            pyvis_net.add_node(e[0].node_name, **node1_options)
            pyvis_net.add_node(e[1].node_name, **node2_options)
            edge_options = get_edge_options(e[2]["object"], default_edge_options)
            pyvis_net.add_edge(e[0].node_name, e[1].node_name, **edge_options)


def get_node_options(nx_node_options, node, default_node_options):
    node_options = default_node_options.copy()
    node_options["label"] = nx_node_options["name"]
    node_options["color"] = nx_node_options["color"]

    if isinstance(node, Server):
        server = node
        title = f"[{server.specs.cpu} CPUs, {server.specs.memory} GB RAM, {server.specs.storage} GB Storage]"
        node_options["title"] = title
        if server.hosted_virtual_machines:
            node_options["title"] +=" \n"
            for vnf in server.hosted_virtual_machines:
                node_options["title"] += f" {vnf.node_name} \n"

    elif isinstance(node, Router):
        router = node

        if router.is_gateway:
            title = f"Gateway Router"
        else:
            title = f"Router"
        node_options["title"] = title
    return node_options


def get_edge_options(nx_edge, default_edge_options):
    link = nx_edge
    bw = link.link_specs.available_bandwidth
    prop_delay = link.link_specs.propagation_delay
    prop_delay_str = "{:.2e}".format(prop_delay)
    edge_options = default_edge_options.copy()
    edge_options["title"] = f"[{bw} Mbps, {prop_delay_str} s]"
    if bw < 10:
        edge_options["color"] = "red"
    if prop_delay > 1*10**-3:
        edge_options["color"] = "red"
    return edge_options
