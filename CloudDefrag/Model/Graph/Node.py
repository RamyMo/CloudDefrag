from abc import ABC, abstractmethod
from typing import List

from CloudDefrag.Logging.Logger import Logger
from CloudDefrag.Model.Graph.Link import VirtualLink
from CloudDefrag.Model.Graph.Specs import Specs
from CloudDefrag.Model.Graph.VNF import VNF
import gurobipy as gp



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
        self._used_specs = Specs(cpu=0, memory=0, storage=0)
        self._server_cost_coefficient = kwargs["server_cost_coefficient"] if "server_cost_coefficient" in kwargs \
            else 1.0
        Logger.log.info(f"Created a server {self.node_name}. Specs: [CPUs: {self.specs.cpu},"
                        f" Memory: {self.specs.memory}(GBs), Storage: {self.specs.storage}(GBs)]")

        self._server_cpu_constr = None
        self._server_memory_constr = None
        self._server_storage_constr = None

    def __str__(self) -> str:
        return f"{self.node_name}"

    @property
    def server_cpu_constrs(self):
        return self._server_cpu_constrs

    @server_cpu_constrs.setter
    def server_cpu_constrs(self, value):
        self._server_cpu_constrs = value

    @property
    def server_memory_constrs(self):
        return self._server_memory_constrs

    @server_memory_constrs.setter
    def server_memory_constrs(self, value):
        self._server_memory_constrs = value

    @property
    def server_storage_constrs(self):
        return self._server_storage_constrs

    @server_storage_constrs.setter
    def server_storage_constrs(self, value):
        self._server_storage_constrs = value

    @property
    def hosted_virtual_machines(self) -> list:
        return self._hosted_virtual_machines

    @hosted_virtual_machines.setter
    def hosted_virtual_machines(self, value: list):
        self._hosted_virtual_machines = value

    @property
    def used_specs(self) -> Specs:
        return self._used_specs

    @property
    def available_specs(self) -> Specs:
        available_cpu = self.specs.cpu - self.used_specs.cpu
        available_memory = self.specs.memory - self.used_specs.memory
        available_storage = self.specs.storage - self.used_specs.storage
        return Specs(cpu=available_cpu, memory=available_memory, storage=available_storage)

    @property
    def server_cost_coefficient(self) -> float:
        return self._server_cost_coefficient

    @server_cost_coefficient.setter
    def server_cost_coefficient(self, value: float):
        self._server_cost_coefficient = value

    def can_server_host_vm(self, vm: Node) -> bool:
        required_cpu = vm.specs.cpu
        required_memory = vm.specs.memory
        required_storage = vm.specs.storage

        available_cpu = self.available_specs.cpu
        available_memory = self.available_specs.memory
        available_storage = self.available_specs.storage

        if available_cpu >= required_cpu and available_memory >= required_memory and available_storage >= \
                required_storage:
            return True
        else:
            return False

    def add_virtual_machine(self, vm):
        if vm in self._hosted_virtual_machines:
            Logger.log.warning(f"Virtual Machine {vm.node_name} is already hosted at {self.node_name}!")
        else:
            if self.can_server_host_vm(vm):
                self._hosted_virtual_machines.append(vm)
                self.used_specs.increase_specs_by(vm.specs)
                vm.host_server = self
                Logger.log.info(f"Server {self.node_name} hosts Virtual Machine {vm.node_name}")
                Logger.log_vm_resources_requirement_info(vm)
                Logger.log_available_resources_info(self)
            else:
                Logger.log_server_cannot_host_vm_resources_warning(self, vm)

    def remove_virtual_machine(self, vm):
        if vm in self._hosted_virtual_machines:
            self._hosted_virtual_machines.remove(vm)
            self.used_specs.decrease_specs_by(vm.specs)
            vm.host_server = None
            Logger.log.info(f"Virtual Machine {vm.node_name} is now removed from host {self.node_name}")
            Logger.log_available_resources_info(self)

        else:
            Logger.log.warning(f"Can't Remove: Virtual Machine {vm.node_name} is not hosted at {self.node_name}!")

    def reset(self):
        hosted_vms = self._hosted_virtual_machines.copy()
        for vm in hosted_vms:
            self.remove_virtual_machine(vm)


class Router(PhysicalNode):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._is_gateway = kwargs["is_gateway"] if "is_gateway" in kwargs else None
        Logger.log.info(f"Created a Router named {self.node_name}")

    def __str__(self) -> str:
        return f"{self.node_name}"

    @property
    def is_gateway(self) -> bool:
        return self._is_gateway

    @is_gateway.setter
    def is_gateway(self, value: bool):
        self._is_gateway = value


class Switch(PhysicalNode):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Logger.log.info(f"Created a Switch {self.node_name}")


class VirtualNode(Node, ABC):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class VirtualMachine(VirtualNode):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._host_server = kwargs["host_server"] if "host_server" in kwargs else None
        self._hosted_vnfs = kwargs["hosted_vnf"] if "hosted_vnf" in kwargs else []
        self._connected_virtual_machines = kwargs["connected_virtual_machines"] if "connected_virtual_machines" \
                                                                                   in kwargs else []
        self._attached_vlinks = kwargs["attached_vlinks"] if "attached_vlinks" in kwargs else []
        self._virtual_machines_link_map = kwargs["virtual_machines_link_map"] if "virtual_machines_link_map" \
                                                                                 in kwargs else {}
        self._vm_revenue_coeff = kwargs["vm_revenue_coeff"] if "vm_revenue_coeff" in kwargs else 1.0
        self._vm_migration_coeff = kwargs["vm_migration_coeff"] if "vm_migration_coeff" in kwargs else 1.0
        Logger.log.info(f"Created a virtual machine {self.node_name}. Requires: [CPUs: {self.specs.cpu},"
                        f" Memory: {self.specs.memory}(GBs), Storage: {self.specs.storage}(GBs)]")

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
    def host_server(self, host: Server):
        self._host_server = host

    @property
    def connected_virtual_machines(self):
        return self._connected_virtual_machines

    @connected_virtual_machines.setter
    def connected_virtual_machines(self, value):
        self._connected_virtual_machines = value

    @property
    def attached_vlinks(self):
        return self._attached_vlinks

    @attached_vlinks.setter
    def attached_vlinks(self, value):
        self._attached_vlinks = value

    @property
    def virtual_machines_link_map(self):
        return self._virtual_machines_link_map

    @virtual_machines_link_map.setter
    def virtual_machines_link_map(self, value):
        self._virtual_machines_link_map = value

    @property
    def vm_revenue_coeff(self) -> float:
        return self._vm_revenue_coeff

    @vm_revenue_coeff.setter
    def vm_revenue_coeff(self, value: float):
        self._vm_revenue_coeff = value

    @property
    def vm_migration_coeff (self) -> float:
        return self._vm_migration_coeff

    @vm_migration_coeff .setter
    def vm_migration_coeff (self, value: float):
        self._vm_migration_coeff = value

    def connect_to_vm(self, vm, vlink: VirtualLink):
        if vm not in self._connected_virtual_machines:
            self._connected_virtual_machines.append(vm)
        if self not in vm.connected_virtual_machines:
            vm.connected_virtual_machines.append(self)
        if vlink not in self._attached_vlinks:
            self._attached_vlinks.append(vlink)
        if vlink not in vm.attached_vlinks:
            vm.attached_vlinks.append(vlink)
        self._virtual_machines_link_map[vm] = vlink
        vm.virtual_machines_link_map[self] = vlink

    def migrate_to_host(self, new_host: Server):
        Logger.log.info(f"Migrate virtual machine {self.node_name} from {self.host_server.node_name}"
                        f" to {new_host.node_name}")
        self.host_server.remove_virtual_machine(self)
        new_host.add_virtual_machine(self)


class VirtualRouter(VirtualNode):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class VirtualSwitch(VirtualNode):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
