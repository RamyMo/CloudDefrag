import networkx as nx
from abc import ABC, abstractmethod


class EnhancedGraph(nx.Graph, ABC):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


shortest_path = nx.shortest_path
