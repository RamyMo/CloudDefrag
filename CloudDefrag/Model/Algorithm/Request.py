import itertools
from abc import ABC

from CloudDefrag.Model.Graph.Link import PhysicalLink, VirtualLink
from CloudDefrag.Model.Graph.Node import VirtualMachine, Node, Router
from CloudDefrag.Model.Graph.Network import VirtualNetwork, PhysicalNetwork
import gurobipy as gp


class VMRequest(ABC):
    _latest_request_id = 0

    @classmethod
    def get_new_request_id(cls):
        return cls._latest_request_id + 1

    def __init__(self, virtual_net: VirtualNetwork, physical_net: PhysicalNetwork, **kwargs) -> None:
        self._virtual_net = virtual_net
        self._physical_net = physical_net
        self._e2e_delay = kwargs["e2e_delay"] if "e2e_delay" in kwargs else None
        self._gateway_router = self._virtual_net.get_gateway_router()
        VMRequest._latest_request_id += 1
        self._request_id = VMRequest._latest_request_id
        self._e2e_delay_constrs = None

    @property
    def e2e_delay_constr(self):
        return self._e2e_delay_constrs

    @e2e_delay_constr.setter
    def e2e_delay_constr(self, value):
        self._e2e_delay_constrs = value

    @property
    def request_id(self) -> int:
        return self._request_id

    @property
    def vm_net(self) -> VirtualNetwork:
        return self._virtual_net

    @vm_net.setter
    def vm_net(self, value: VirtualNetwork):
        self._virtual_net = value

    @property
    def physical_net(self) -> PhysicalNetwork:
        return self._physical_net

    @physical_net.setter
    def physical_net(self, value: PhysicalNetwork):
        self._physical_net = value

    @property
    def e2e_delay(self) -> float:
        return self._e2e_delay

    @e2e_delay.setter
    def e2e_delay(self, value: float):
        self._e2e_delay = value

    @property
    def gateway_router(self) -> Router:
        return self._gateway_router


class HostedVMRequest(VMRequest):

    def __init__(self, virtual_net: VirtualNetwork, physical_net: PhysicalNetwork, **kwargs) -> None:
        super().__init__(virtual_net, physical_net, **kwargs)

        # VMs
        self._hosted_vms = self._virtual_net.get_vms()
        self._hosted_vms_names = [v.node_name for v in self._hosted_vms]
        self._hosted_vms_dict = {v.node_name: v for v in self._hosted_vms}
        self._hosted_vms_servers_assign_dict = {}  # Assignment of all existing VMs
        self._hosted_vms_servers_migrate_cost_dict = {}  # Migration cost
        self.__create_hosted_vms_dicts()
        self._hosted_vms_combinations, self._hosted_vms_servers_migration_cost = \
            gp.multidict(self._hosted_vms_servers_migrate_cost_dict)
        # Hosted VMs Assignment variables after migration
        self._y = None

        # vLinks
        self._hosted_vlinks = self._virtual_net.get_links()
        self._hosted_vlinks_names = [v.name for v in self._hosted_vlinks]
        self._hosted_vlinks_dict = {v.name: v for v in self._hosted_vlinks}
        self._hosted_vlink_assign_dict = {}  # Assignment of all existing vlinks
        self._hosted_vlink_migrate_cost_dict = {}
        self._hosted_vlink_prop_delay_dict = {}  # Prop delay of assignment of all new vlinks to plinks
        self.__create_hosted_vlinks_dicts()
        self._hosted_vlinks_combinations, self._hosted_vlinks_migration_cost = \
            gp.multidict(self._hosted_vlink_migrate_cost_dict)
        _, self._hosted_vlinks_prop_delay = gp.multidict(self._hosted_vlink_prop_delay_dict)
        # Hosted vLinks Assignment variables after migration
        self._vL = None

    @property
    def hosted_vlinks_prop_delay(self):
        return self._hosted_vlinks_prop_delay

    @hosted_vlinks_prop_delay.setter
    def hosted_vlinks_prop_delay(self, value):
        self._hosted_vlinks_prop_delay = value

    def __create_hosted_vms_dicts(self):
        hosted_vms_servers_combination = list(itertools.product(self._hosted_vms, self.physical_net.get_servers()))
        for i in hosted_vms_servers_combination:
            if i[0].host_server == i[1]:
                self._hosted_vms_servers_assign_dict[(i[0].node_name, i[1].node_name)] = 1
                self._hosted_vms_servers_migrate_cost_dict[(i[0].node_name, i[1].node_name)] = 0
            else:
                self._hosted_vms_servers_assign_dict[(i[0].node_name, i[1].node_name)] = 0
                self._hosted_vms_servers_migrate_cost_dict[(i[0].node_name, i[1].node_name)] = i[0].vm_migration_coeff

    def __create_hosted_vlinks_dicts(self):
        hosted_vlinks_combination = list(itertools.product(self._hosted_vlinks, self.physical_net.get_links()))
        for i in hosted_vlinks_combination:
            self._hosted_vlink_prop_delay_dict[(i[0].name, i[1].name)] = i[1].link_specs.propagation_delay
            if i[1] in i[0].hosting_physical_links:
                self._hosted_vlink_assign_dict[(i[0].name, i[1].name)] = 1
                self._hosted_vlink_migrate_cost_dict[(i[0].name, i[1].name)] = 0
            else:
                self._hosted_vlink_assign_dict[(i[0].name, i[1].name)] = 0
                self._hosted_vlink_migrate_cost_dict[(i[0].name, i[1].name)] = i[0].vlink_migration_coeff

    @property
    def hosted_vlinks_names(self):
        return self._hosted_vlinks_names

    @property
    def hosted_vms_assign_vars(self):
        return self._y

    @hosted_vms_assign_vars.setter
    def hosted_vms_assign_vars(self, value):
        self._y = value

    @property
    def hosted_vlinks_assign_vars(self):
        return self._vL

    @hosted_vlinks_assign_vars.setter
    def hosted_vlinks_assign_vars(self, value):
        self._vL = value

    @property
    def hosted_vms_combinations(self):
        return self._hosted_vms_combinations

    @property
    def hosted_vms_servers_assign_dict(self):
        return self._hosted_vms_servers_assign_dict

    @property
    def hosted_vms_dict(self):
        return self._hosted_vms_dict

    @property
    def hosted_vms_names(self):
        return self._hosted_vms_names

    @property
    def hosted_vlinks_combinations(self):
        return self._hosted_vlinks_combinations

    @property
    def hosted_vlink_assign_dict(self):
        return self._hosted_vlink_assign_dict

    @property
    def hosted_vlinks_dict(self):
        return self._hosted_vlinks_dict

class NewVMRequest(VMRequest):

    def __init__(self, virtual_net: VirtualNetwork, physical_net: PhysicalNetwork, **kwargs) -> None:
        super().__init__(virtual_net, physical_net, **kwargs)

        # VMs
        self._requested_vms = self._virtual_net.get_vms()
        self._requested_vms_names = [v.node_name for v in self._requested_vms]
        self._requested_vms_dict = {v.node_name: v for v in self._requested_vms}
        self._requested_vms_servers_assign_dict = {}  # Assignment of all new VMs requests
        self._requested_vms_servers_cost_dict = {}  # Cost of hosting VMs at servers dict
        self._requested_vms_servers_revenue_dict = {}  # Revenue of hosting VMs at servers dict
        self.__create_requested_vms_dicts()
        self._requested_vms_combinations, self._requested_vms_servers_cost = \
            gp.multidict(self._requested_vms_servers_cost_dict)
        _, self._requested_vms_servers_revenue = gp.multidict(self._requested_vms_servers_revenue_dict)
        # New VMs Assignment variables
        self._x = None


        # vLinks
        self._requested_vlinks = self._virtual_net.get_links()
        self._requested_vlinks_names = [v.name for v in self._requested_vlinks]
        self._requested_vlinks_dict = {v.name: v for v in self._requested_vlinks}
        self._requested_vlink_assign_dict = {}  # Assignment of all new vlinks
        self._requested_vlink_cost_dict = {}  # Cost of assignment of all new vlinks
        self._requested_vlink_revenue_dict = {}  # Revenue of assignment of all new vlinks
        self._requested_vlink_prop_delay_dict = {}  # Prop delay of assignment of all new vlinks to plinks
        self.__create_requested_vlinks_dicts()
        self._requested_vlinks_combinations, self._requested_vlinks_cost = \
            gp.multidict(self._requested_vlink_cost_dict)
        _, self._requested_vlinks_revenue = gp.multidict(self._requested_vlink_revenue_dict)
        _, self._requested_vlinks_prop_delay = gp.multidict(self._requested_vlink_prop_delay_dict)
        # New vlinks Assignment variables
        self._new_vl = None

    @property
    def requested_vlinks_prop_delay(self):
        return self._requested_vlinks_prop_delay

    @requested_vlinks_prop_delay.setter
    def requested_vlinks_prop_delay(self, value):
        self._requested_vlinks_prop_delay = value
    @property
    def requested_vlinks_names(self):
        return self._requested_vlinks_names

    @property
    def requested_vlinks_dict(self):
        return self._requested_vlinks_dict
    @property
    def requested_vlinks_cost(self):
        return self._requested_vlinks_cost
    @property
    def new_vms_assign_vars(self):
        return self._x

    @new_vms_assign_vars.setter
    def new_vms_assign_vars(self, value):
        self._x = value

    @property
    def new_vlinks_assign_vars(self):
        return self._new_vl

    @new_vlinks_assign_vars.setter
    def new_vlinks_assign_vars(self, value):
        self._new_vl = value

    def __create_requested_vms_dicts(self):
        requested_vms_servers_combination = list(itertools.product(self._requested_vms,
                                                                   self.physical_net.get_servers()))
        for i in requested_vms_servers_combination:
            self._requested_vms_servers_assign_dict[(i[0].node_name, i[1].node_name)] = 0
            self._requested_vms_servers_cost_dict[(i[0].node_name, i[1].node_name)] = i[1].server_cost_coefficient
            self._requested_vms_servers_revenue_dict[(i[0].node_name, i[1].node_name)] = i[0].vm_revenue_coeff

    def __create_requested_vlinks_dicts(self):
        requested_vlinks_combination = list(itertools.product(self._requested_vlinks, self.physical_net.get_links()))
        for i in requested_vlinks_combination:
            self._requested_vlink_assign_dict[(i[0].name, i[1].name)] = 0
            self._requested_vlink_cost_dict[(i[0].name, i[1].name)] = i[1].link_cost_coefficient
            self._requested_vlink_revenue_dict[(i[0].name, i[1].name)] = i[0].vlink_revenue_coeff
            self._requested_vlink_prop_delay_dict[(i[0].name, i[1].name)] = i[1].link_specs.propagation_delay

    @property
    def requested_vlinks_combinations(self):
        return self._requested_vlinks_combinations
    @property
    def requested_vms_combinations(self):
        return self._requested_vms_combinations

    @property
    def requested_vms_servers_revenue(self):
        return self._requested_vms_servers_revenue

    @property
    def requested_vms_dict(self):
        return self._requested_vms_dict

    @property
    def requested_vms_names(self):
        return self._requested_vms_names
