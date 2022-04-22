from abc import ABC, abstractmethod
from typing import List

from CloudDefrag.Model.Graph.Specs import Specs
from CloudDefrag.Model.Graph.VNF import VNF


class Node(ABC):

    def __init__(self, **kwargs):
        self._specs = kwargs["specs"] if "specs" in kwargs else None
        self._node_name = kwargs["node_name"] if "node_name" in kwargs else None
        self._node_label = kwargs["node_label"] if "node_label" in kwargs else None

    @property
    def specs(self) -> Specs:
        return self._specs

    @specs.setter
    def specs(self, value: Specs):
        self._specs = value

    @property
    def node_name(self) -> str:
        return self._node_name

    @node_name.setter
    def node_name(self, value: str):
        self._node_name = value

    @property
    def node_label(self) -> str:
        return self._node_label

    @node_label.setter
    def node_label(self, value: str):
        self._node_label = value

    def __str__(self) -> str:
        return self._node_name


class PhysicalNode(Node, ABC):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Server(PhysicalNode):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._hosted_virtual_machines = kwargs["hosted_virtual_machines"] if "hosted_virtual_machines" in kwargs \
            else []

    @property
    def hosted_virtual_machines(self) -> list:
        return self._hosted_virtual_machines

    @hosted_virtual_machines.setter
    def hosted_virtual_machines(self, value: list):
        self._hosted_virtual_machines = value


class Router(PhysicalNode):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._is_gateway = kwargs["is_gateway"] if "is_gateway" in kwargs else None

    @property
    def is_gateway(self) -> bool:
        return self._is_gateway

    @is_gateway.setter
    def is_gateway(self, value: bool):
        self._is_gateway = value


class Switch(PhysicalNode):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class VirtualNode(Node, ABC):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class VirtualMachine(VirtualNode):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._host_server = kwargs["host_server"] if "host_server" in kwargs else None
        self._hosted_vnfs = kwargs["hosted_vnf"] if "hosted_vnf" in kwargs else []

    @property
    def hosted_vnfs(self) -> List[VNF]:
        return self._hosted_vnfs

    @hosted_vnfs.setter
    def hosted_vnfs(self, value: List[VNF]):
        self._hosted_vnfs = value

    @property
    def host_server(self) -> Server:
        return self._host_server

    @host_server.setter
    def host_server(self, value: Server):
        self._host_server = value


class VirtualRouter(VirtualNode):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class VirtualSwitch(VirtualNode):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
