from typing import List
import itertools
import gurobipy as gp
from CloudDefrag.Model.Graph import Network
from CloudDefrag.Model.Graph.Node import VirtualMachine


class HouILP:
    def __init__(self, net: Network, requests: List[VirtualMachine], **kwargs) -> None:
        self._model = gp.Model("HouILP")
        self._network = net
        self._requests = requests
        self._servers = net.servers
        self._hosted_vms = kwargs["hosted_vms"] if "hosted_vms" in kwargs else []
        self._hosted_vms_servers_assign_dict = {}
        self._hosted_vms_servers_migrate_dict = {}
        self._hosted_vms_servers_combination = list(itertools.product(self._hosted_vms, self._servers))
        for i in self._hosted_vms_servers_combination:
            self._hosted_vms_servers_migrate_dict[(i[0].node_name, i[1].node_name)] = 1
            if i[0].host_server == i[1]:
                self._hosted_vms_servers_assign_dict[(i[0].node_name, i[1].node_name)] = 1
            else:
                self._hosted_vms_servers_assign_dict[(i[0].node_name, i[1].node_name)] = 0
        del self._hosted_vms_servers_combination

