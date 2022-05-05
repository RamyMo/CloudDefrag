from typing import List
import itertools
import gurobipy as gp
from CloudDefrag.Model.Graph import Network
from CloudDefrag.Model.Graph.Node import VirtualMachine
from CloudDefrag.Logging.Logger import Logger


class HouILP:
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
        self._hosted_vms_dict = {v.node_name: v for v in self._hosted_vms}
        self._requested_vms_names = [v.node_name for v in requested_vms]
        self._requested_vms_dict = {v.node_name: v for v in requested_vms}
        self._hosted_vms_servers_assign_dict = {}  # Assignment of all existing VMs
        self._hosted_vms_servers_migrate_cost_dict = {}  # Assignment of all existing VMs after VM migrations
        self._requested_vms_servers_assign_dict = {}  # Assignment of all new VMs requests
        self._requested_vms_servers_cost_dict = {}  # Cost of hosting VMs at servers dict
        self._requested_vms_servers_revenue_dict = {}  # Revenue of hosting VMs at servers dict
        self.__create_hosted_vms_dicts()
        self.__create_requested_vms_dicts()
        Logger.log.info(f"Created an instance of HouILP algorithm for model {self._model_name}.")

        self._hosted_vms_combinations, self._hosted_vms_servers_migration_cost = \
            gp.multidict(self._hosted_vms_servers_migrate_cost_dict)

        self._requested_vms_combinations, self._requested_vms_servers_cost = \
            gp.multidict(self._requested_vms_servers_cost_dict)
        _, self._requested_vms_servers_revenue = gp.multidict(self._requested_vms_servers_revenue_dict)

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

    def __create_decision_variables(self):
        self._x = self._model.addVars(self._requested_vms_combinations, name="new_assign", vtype=gp.GRB.BINARY)
        self._y = self._model.addVars(self._hosted_vms_combinations, name="cur_assign", vtype=gp.GRB.BINARY)

    def __create_objective_function(self):
        revenue = self._x.prod(self._requested_vms_servers_revenue)
        cost = gp.quicksum((self._hosted_vms_servers_assign_dict[v, s] * (1 - self._y[v, s])) *
                           self._hosted_vms_dict[v].vm_migration_coeff for v, s in self._hosted_vms_combinations)
        self._model.setObjective(revenue - cost, gp.GRB.MAXIMIZE)

    def __create_resource_capacity_constrs(self):
        # Resource Capacity Constraints
        server_cpu_constrs = self._model.addConstrs(
            (gp.quicksum((self._y[v, s] * self._hosted_vms_dict[v].specs.cpu) for v in
                         self._hosted_vms_names)
             +
             gp.quicksum((self._x[v, s] * self._requested_vms_dict[v].specs.cpu) for v in
                         self._requested_vms_names)
             <= self._servers_dict[s].specs.cpu for s in self._servers_names), name='server_cpu_cap')

        server_mem_constrs = self._model.addConstrs(
            (gp.quicksum((self._y[v, s] * self._hosted_vms_dict[v].specs.memory) for v in
                         self._hosted_vms_names)
             +
             gp.quicksum((self._x[v, s] * self._requested_vms_dict[v].specs.memory) for v in
                         self._requested_vms_names)
             <= self._servers_dict[s].specs.memory for s in self._servers_names), name='server_memory_cap')

        server_storage_constrs = self._model.addConstrs(
            (gp.quicksum((self._y[v, s] * self._hosted_vms_dict[v].specs.storage) for v in
                         self._hosted_vms_names)
             +
             gp.quicksum((self._x[v, s] * self._requested_vms_dict[v].specs.storage) for v in
                         self._requested_vms_names)
             <= self._servers_dict[s].specs.storage for s in self._servers_names), name='server_storage_cap')

    def __create_single_host_constrs(self):
        vm_host_requested_constrs = self._model.addConstrs((self._x.sum(v, '*') <= 1 for v in self._requested_vms_names)
                                                           ,name='requested_vm_single_host')

        vm_host_hosted_constrs = self._model.addConstrs((self._y.sum(v, '*') == 1 for v in self._hosted_vms_names)
                                                           , name='hosted_vm_single_host')

    def __create_requested_vms_dicts(self):
        self._requested_vms_servers_combination = list(itertools.product(self._requested_vms, self._servers))
        for i in self._requested_vms_servers_combination:
            self._requested_vms_servers_assign_dict[(i[0].node_name, i[1].node_name)] = 0
            self._requested_vms_servers_cost_dict[(i[0].node_name, i[1].node_name)] = i[1].server_cost_coefficient
            self._requested_vms_servers_revenue_dict[(i[0].node_name, i[1].node_name)] = i[0].vm_revenue_coeff
        del self._requested_vms_servers_combination

    def __create_hosted_vms_dicts(self):
        hosted_vms_servers_combination = list(itertools.product(self._hosted_vms, self._servers))
        for i in hosted_vms_servers_combination:
            self._hosted_vms_servers_migrate_cost_dict[(i[0].node_name, i[1].node_name)] = i[0].vm_migration_coeff
            if i[0].host_server == i[1]:
                self._hosted_vms_servers_assign_dict[(i[0].node_name, i[1].node_name)] = 1
            else:
                self._hosted_vms_servers_assign_dict[(i[0].node_name, i[1].node_name)] = 0

    # Run optimization engine
    def solve(self, **kwargs):
        self._model.optimize()
        Logger.log.info(f"Solving problem model {self._model_name} using HouILP...")
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
        print(f"Runtime: {self._model.getAttr(gp.GRB.Attr.Runtime)} seconds" )

    def apply_result(self):
        Logger.log.info(f"Apply the problem solution to the infrastructure...")
        # Start Migration
        Logger.log.info(f"Start VM Migration...")
        for v, s in self._hosted_vms_combinations:
            if self._y[v, s].x == 1:
                if self._hosted_vms_servers_assign_dict[v, s] != 1:
                    # Migrate v to s
                    self._hosted_vms_dict[v].migrate_to_host(self._servers_dict[s])
        Logger.log.info(f"Assign new VMs...")
        # Assign new VMs
        for v, s in self._requested_vms_combinations:
            if self._x[v, s].x == 1:
                self._servers_dict[s].add_virtual_machine(self._requested_vms_dict[v])


