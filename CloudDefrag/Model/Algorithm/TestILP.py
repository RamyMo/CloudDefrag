from typing import List
import itertools
import gurobipy as gp
from CloudDefrag.Model.Graph import Network
from CloudDefrag.Model.Graph.Node import VirtualMachine


class TestILP:
    def __init__(self, net: Network, requested_vms: List[VirtualMachine], **kwargs) -> None:
        self._model_name = kwargs["model_name"] if "model_name" in kwargs else "HouILP Model"
        self._model = gp.Model(self._model_name)
        self._network = net
        self._requested_vms = requested_vms
        self._servers = net.get_servers
        self._servers_names = [server.node_name for server in net.get_servers]
        self._servers_dict = {server.node_name: server for server in net.get_servers}
        self._hosted_vms = kwargs["hosted_vms"] if "hosted_vms" in kwargs else []
        self._hosted_vms_names = [v.node_name for v in kwargs["hosted_vms"]] if "hosted_vms" in kwargs else []
        self._requested_vms_names = [v.node_name for v in requested_vms]
        self._requested_vms_dict = {v.node_name: v for v in requested_vms}
        self._hosted_vms_servers_assign_dict = {}  # Assignment of all existing VMs
        self._hosted_vms_servers_migrate_dict = {}  # Assignment of all existing VMs after VM migrations
        self._requested_vms_servers_assign_dict = {}  # Assignment of all new VMs requests
        self._requested_vms_servers_cost_dict = {}  # Assignment of all new VMs requests
        self.__create_hosted_vms_dicts()
        self.__create_requested_vms_dicts()
        self._requested_vms_combinations, self._requested_vms_servers_cost = \
            gp.multidict(self._requested_vms_servers_cost_dict)

        self.__create_problem_model()
        # Save model for inspection
        self._model.write(f'output/{self._model_name}.lp')

    @property
    def model(self) -> gp.Model:
        return self._model

    @model.setter
    def model(self, value: gp.Model):
        self._model = value

    def __create_problem_model(self):
        # Create decision variables for the model
        self.__create_decision_variables()

        # Objective: minimize total all new VMs assignments
        self.__create_objective_function()

        # Servers Resource Capacity Constraints
        self.__create_resource_capacity_constrs()

        # VM Single Host Constraints
        # Ensure that each VM is hosted by exactly one server
        self.__create_single_host_constrs()

    def __create_single_host_constrs(self):
        self._vm_host_constrs = self._model.addConstrs((self._x.sum(v, '*') == 1 for v in self._requested_vms_names),
                                                       name='vm_single_host')

    def __create_resource_capacity_constrs(self):
        # Resource Capacity Constraints
        server_cpu_constrs = self._model.addConstrs(
            (gp.quicksum((self._x[v, s] * self._requested_vms_dict[v].specs.cpu) for v in
                         self._requested_vms_names) <= self._servers_dict[s].available_specs.cpu
             for s in self._servers_names), name='server_cpu_cap')
        server_mem_constrs = self._model.addConstrs(
            (gp.quicksum((self._x[v, s] * self._requested_vms_dict[v].specs.memory) for v in
                         self._requested_vms_names) <=
             self._servers_dict[s].available_specs.memory
             for s in self._servers_names), name='server_memory_cap')
        server_storage_constrs = self._model.addConstrs(
            (gp.quicksum((self._x[v, s] * self._requested_vms_dict[v].specs.storage) for v in
                         self._requested_vms_names) <=
             self._servers_dict[s].available_specs.storage
             for s in self._servers_names), name='server_storage_cap')

    def __create_objective_function(self):
        self._model.setObjective(self._x.prod(self._requested_vms_servers_cost), gp.GRB.MINIMIZE)

    def __create_decision_variables(self):
        self._x = self._model.addVars(self._requested_vms_combinations, name="assign", vtype=gp.GRB.BINARY)

    def __create_requested_vms_dicts(self):
        self._requested_vms_servers_combination = list(itertools.product(self._requested_vms, self._servers))
        for i in self._requested_vms_servers_combination:
            self._requested_vms_servers_assign_dict[(i[0].node_name, i[1].node_name)] = 0
            self._requested_vms_servers_cost_dict[(i[0].node_name, i[1].node_name)] = i[1].server_cost_coefficient
        del self._requested_vms_servers_combination

    def __create_hosted_vms_dicts(self):
        hosted_vms_servers_combination = list(itertools.product(self._hosted_vms, self._servers))
        for i in hosted_vms_servers_combination:
            if i[0].host_server == i[1]:
                self._hosted_vms_servers_assign_dict[(i[0].node_name, i[1].node_name)] = 1
                self._hosted_vms_servers_migrate_dict[(i[0].node_name, i[1].node_name)] = 1
            else:
                self._hosted_vms_servers_assign_dict[(i[0].node_name, i[1].node_name)] = 0
                self._hosted_vms_servers_migrate_dict[(i[0].node_name, i[1].node_name)] = 0

    # Run optimization engine
    def solve(self, **kwargs):
        self._model.optimize()
        if kwargs["display_result"]:
            self.display_result()

    def display_result(self):
        # Display optimal values of decision variables
        print("Decision Variables:")
        for v in self._model.getVars():
            if v.x > 1e-6:
                print(f"{v.varName} = {v.x}")
        # Display optimal total matching score
        print('Total cost: ', self._model.objVal)
