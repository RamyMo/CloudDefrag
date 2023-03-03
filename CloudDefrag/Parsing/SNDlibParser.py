import networkx as nx
import pyvis

from CloudDefrag.Model.Graph.Link import PhysicalLink, LinkSpecs
from CloudDefrag.Model.Graph.Network import PhysicalNetwork
from CloudDefrag.Model.Graph.Node import Router, Server
from CloudDefrag.Model.Graph.Specs import Specs
from CloudDefrag.Visualization.Visualizer import from_nx_to_pyvis


class SNDlibParser:

    def __init__(self, net_name) -> None:
        self.net_name = net_name
        self.net_path = f"input/SNDlib/{self.net_name}/{self.net_name}.gml"
        self.raw_graph = nx.read_gml(self.net_path)
        self.net = PhysicalNetwork(name=self.net_name)
        self.__parse_network_nodes()
        self.__parse_network_connections()
        self.__save_interactive_visual()

    def __parse_network_nodes(self):
        net = self.net
        for node in self.raw_graph:
            type = "Server"
            name = node
            label = "server"
            cpu = 1
            memory = 1
            storage = 1
            is_gateway = False
            weight = 0
            if type == "Server":
                self.__parse_server(name, label, cpu, memory, storage, weight)
            elif type == "Router":
                self.__parse_router(name, label, is_gateway)

    def __parse_server(self, name: str, label: str, cpu: int, memory: int, storage: int, weight: int):
        net = self.net
        s = Server(specs=Specs(cpu=cpu, memory=memory, storage=storage), node_name=name, node_label=label,
                   weight=weight)
        net.add_network_node(s, name=name, label=label, color="gold")

    def __parse_router(self, name: str, label: str, is_gateway: bool):
        net = self._net
        w = Router(node_name=name, node_label=label, is_gateway=is_gateway, weight=0)
        if is_gateway:
            net.add_network_node(w, name=name, label=label, color="lightskyblue")
        else:
            net.add_network_node(w, name=name, label=label, color="blue")

    def __parse_network_connections(self):
        for edge in self.raw_graph.edges:
            net = self.net
            weight = 0
            source = edge[0]
            target = edge[1]
            bw = 100
            prop_delay = 1 * (10 ** -6)
            net_dict = net.get_node_dict()
            n1 = net_dict[source]
            n2 = net_dict[target]
            pl = net.add_network_edge(PhysicalLink(source=n1, target=n2, weight=weight,
                                                   link_specs=LinkSpecs(bandwidth=bw,
                                                                        propagation_delay=prop_delay)))

    def __save_interactive_visual(self):
        """
           Creates an interactive visualization of the network using pyvis library and saves it as an HTML file.

           Args:
           - self: an instance of the Network class

           Returns: None
           """
        # create vis network
        vis_net = pyvis.network.Network(notebook=True)
        # vis_net.from_nx(self._net)
        from_nx_to_pyvis(vis_net, nx_graph=self.net)

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

        # set nodes locations according to SNDlib
        for key, value in vis_net.node_map.items():

            x = self.raw_graph.nodes[key]["graphics"]["x"]
            y = self.raw_graph.nodes[key]["graphics"]["y"]
            vis_net.get_node(key)["x"] = x
            vis_net.get_node(key)["y"] = y

        vis_net.show(f"input/SNDlib/{self.net_name}/{self.net_name}.html")
