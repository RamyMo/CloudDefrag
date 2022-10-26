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

        # vis_net.show_buttons(filter_=['physics'])
        # vis_net.show_buttons(filter_=['nodes'])
        vis_net.set_options("""
        const options = {
          "physics": {
            "barnesHut": {
              "avoidOverlap": 1
            }
          },
          "nodes": {
            "borderWidth": 7,
            "borderWidthSelected": 17,
            "font": {
              "size": 18
            },
            "shadow": {
              "enabled": true
            },
            "size": null
          }
        }
        """)
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
    default_node_options = {"size": default_node_size}
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
        title = f"[{server.specs.cpu - server.repair_specs.cpu} CPUs, " \
                f"{server.specs.memory - server.repair_specs.memory} GB RAM," \
                f" {server.specs.storage - server.repair_specs.storage} GB Storage]"

        node_options["title"] = title
        if server.is_selected_for_feas_repair:
            node_options["label"] += " : Upgrade"
        if server.is_selected_for_feas_repair:
            node_options["title"] += f" \n Upgrade to: \n[{server.specs.cpu} CPUs, " \
                f"{server.specs.memory} GB RAM," \
                f" {server.specs.storage} GB Storage]"
            node_options["borderWidth"] = 8

        node_options["title"] += f" \n Available: \n [{server.available_specs.cpu} CPUs, " \
                f"{server.available_specs.memory} GB RAM," \
                f" {server.available_specs.storage} GB Storage]"
        if server.hosted_virtual_machines:
            node_options["title"] +=" \n Hosted VNFs: \n"
            for vnf in server.hosted_virtual_machines:
                node_options["title"] += f" {vnf.node_name} \n"
    elif isinstance(node, Router):
        router = node

        if router.is_gateway:
            title = f"Gateway Router"
            type1_requests = router.type1_requests
            num_of_type1 = len(type1_requests)
            type2_requests = router.type2_requests
            num_of_type2 = len(type2_requests)
            type3_requests = router.type3_requests
            num_of_type3 = len(type3_requests)
            node_options["label"] += f" \n [{num_of_type1}, {num_of_type2}, {num_of_type3}]"
            if router.hosted_dummy_vms:
                title += " \n Dummy VNFs: "
            for vm in router.hosted_dummy_vms:
                title += f" \n {vm.node_name}"
        else:
            title = f"Router"
        node_options["title"] = title
    return node_options


def get_edge_options(nx_edge, default_edge_options):
    link = nx_edge
    prop_delay = link.link_specs.propagation_delay
    prop_delay_str = "{:.2e}".format(prop_delay)
    edge_options = default_edge_options.copy()
    edge_options["title"] = f"[{link.link_specs.bandwidth - link.link_repair_specs.available_bandwidth} Mbps, " \
                            f"{prop_delay_str} s]"
    if link.is_selected_for_feas_repair:
        edge_options["label"] = "Upgrade"
        edge_options["title"] += f" \n Upgrade to: \n [{link.link_specs.bandwidth} Mbps, {prop_delay_str} s]"

    if link.link_specs.bandwidth - link.link_repair_specs.available_bandwidth < 10:
        edge_options["color"] = "red"
    if prop_delay > 1*10**-3:
        edge_options["color"] = "red"

    edge_options["title"] += f" \n Available: \n [{link.link_specs.available_bandwidth} Mbps, " \
                            f"{prop_delay_str} s]"
    return edge_options
