import networkx as nx
import matplotlib.pyplot as plt

from CloudDefrag.Model.Graph.Network import PhysicalNetwork


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

