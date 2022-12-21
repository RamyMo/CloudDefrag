from abc import ABC, abstractmethod
from typing import List
import gurobipy as gp

from CloudDefrag.Logging.Logger import Logger
from CloudDefrag.Model.Algorithm.Request import NewVMRequest, HostedVMRequest
from CloudDefrag.Model.Graph.Network import PhysicalNetwork
from CloudDefrag.Model.Graph.Node import DummyVirtualMachine, Server


class Algorithm(ABC):
    """Algorithm abstract class is used for any algorithm that is solved via solver like Guroubi"""

    def __init__(self, net: PhysicalNetwork, new_requests: List[NewVMRequest], hosted_requests: List[HostedVMRequest],
                 **kwargs) \
            -> None:
        self._model_name = kwargs["model_name"] if "model_name" in kwargs else "RamyILP Model"
        self._model = gp.Model(self._model_name)
        self._network = net
        self._hosted_requests = hosted_requests
        self._new_requests = new_requests

        # Physical Network Infrastructure
        self._servers = net.get_servers()
        self._servers_names = [server.node_name for server in self._servers]
        self._servers_dict = {server.node_name: server for server in self._servers}

        self._nodes = net.network_nodes
        self._nodes_names = [node.node_name for node in self._nodes]
        self._nodes_dict = {node.node_name: node for node in self._nodes}

        self._physical_links = net.get_links()
        self._physical_links_names = [vl.name for vl in self._physical_links]
        self._physical_links_dict = net.get_links_dict()

        # Algorithm Results
        self._algorithm_result = AlgorithmResult()
        self.algorithm_result.algorithm_name = self._model_name

        Logger.log.info(f"Created an instance of ILP algorithm for model {self._model_name}.")
        self._create_problem_model()

        # Save model for inspection
        self._model.write(f'output/{self._model_name}.lp')

    @property
    def model(self) -> gp.Model:
        return self._model

    @model.setter
    def model(self, value):
        self._model = value

    # Takes Gurobi model as an input and return True if model is feasible and False o.w
    @property
    def isFeasible(self):
        isFeas = False
        # Current optimization status for the model. Status values are described in the Status Code section.
        # https://www.gurobi.com/documentation/9.5/refman/optimization_status_codes.html#sec:StatusCodes
        # Get  model Status
        status = self._model.Status
        # https://www.gurobi.com/documentation/9.5/refman/dualreductions.html#parameter:DualReductions
        if status == 4:  # Model was proven to be either infeasible or unbounded.
            self._model.Params.DualReductions = 0
            self._model.optimize()
            status = self._model.Status

        if status == 2 or status == 5:  # OPTIMAL or UNBOUNDED
            IIS = []
            isFeas = True

        elif status == 3:  # Model was proven to be infeasible.
            isFeas = False

        return isFeas

    @property
    def algorithm_result(self):
        return self._algorithm_result

    @algorithm_result.setter
    def algorithm_result(self, value):
        self._algorithm_result = value

    @abstractmethod
    def _create_problem_model(self):
        pass

    @abstractmethod
    def _create_decision_variables(self):
        pass

    @abstractmethod
    def _create_objective_function(self):
        pass

    @abstractmethod
    def _create_servers_resource_capacity_constrs(self):
        pass

    @abstractmethod
    def _create_links_bw_capacity_constrs(self):
        pass

    @abstractmethod
    def _create_e2e_delay_constrs(self):
        pass

    @abstractmethod
    def _create_prop_delay_constrs(self):
        pass

    @abstractmethod
    def _create_flow_conservation_constr(self):
        pass

    @abstractmethod
    def _create_single_host_constrs(self):
        pass

    @abstractmethod
    def _create_single_server_constrs(self):
        pass

    @abstractmethod
    def _create_dummy_vm_constrs(self):
        pass

    # Run optimization engine
    def solve(self, **kwargs):
        # Solves return non-integral values for integer variables
        # https://www.gurobi.com/documentation/9.5/refman/integralityfocus.html
        # https://support.gurobi.com/hc/en-us/articles/360012237872-Why-does-Gurobi-sometimes-return-non-integral-values-for-integer-variables-
        self._model.setParam("IntegralityFocus", 1)

        self._model.optimize()
        Logger.log.info(f"Solving problem model {self._model_name} using RamyILP...")
        if self.isFeasible:
            Logger.log.info(f"Model {self._model_name} is feasible")
            self.algorithm_result.is_success = True
            self.algorithm_result.cost = self._model.objVal
            self.algorithm_result.execution_time = self._model.getAttr(gp.GRB.Attr.Runtime)
            if kwargs["display_result"]:
                # TODO: fix print_decision_variables
                if kwargs["print_decision_variables"]:
                    print_decision_variables = True
                else:
                    print_decision_variables = False
                self.display_result(print_decision_variables=print_decision_variables)
        else:
            Logger.log.info(f"Model {self._model_name} is infeasible")
            # print(f"Model {self._model_name} is infeasible")
            self.algorithm_result.is_success = False

    # Display Results
    def display_result(self, **kwargs):
        print("\n*******************************************************")
        print(f"Showing results for model: {self._model_name}")
        # Model properties:
        print(f"Number of Decision Variables: {len(self._model.getVars())}")
        print(f"Number of Constraints: {len(self._model.getConstrs())}")
        # Display optimal values of decision variables
        if kwargs["print_decision_variables"]:
            print("Decision Variables:")
            for v in self._model.getVars():
                if v.x > 1e-6:
                    print(f"{v.varName} = {v.x}")
        # Display optimal total matching score
        print('Total cost: ', self._model.objVal)
        print(f"Runtime: {self._model.getAttr(gp.GRB.Attr.Runtime)} seconds")
        print("*******************************************************\n")

    # Apply results
    def apply_result(self):
        net_node_dict = self._network.get_node_dict()

        Logger.log.info(f"Apply the problem solution to the infrastructure...")

        # Start Migration
        Logger.log.info(f"Start VM Migration...")

        for hosted_req in self._hosted_requests:
            # VMs
            hosted_vms_combinations = hosted_req.hosted_vms_combinations
            y = hosted_req.hosted_vms_assign_vars
            hosted_vms_servers_assign_dict = hosted_req.hosted_vms_servers_assign_dict
            hosted_vms_dict = hosted_req.hosted_vms_dict
            for v, s in hosted_vms_combinations:
                if isinstance(hosted_vms_dict[v], DummyVirtualMachine):
                    continue
                if y[v, s].x == 1:
                    if hosted_vms_servers_assign_dict[v, s] != 1:
                        # Migrate v to s
                        hosted_vms_dict[v].migrate_to_host(self._servers_dict[s])
            # vLinks
            hosted_vlinks_objects_combination = hosted_req.hosted_vlinks_objects_combination
            hosted_vlink_assign_dict = hosted_req.hosted_vlink_assign_dict
            hosted_vlinks_dict = hosted_req.hosted_vlinks_dict
            vL = hosted_req.hosted_vlinks_assign_vars
            for i in hosted_vlinks_objects_combination:
                vl = i[0]  # vLink object
                pl = i[1]  # pLink object
                vl_name = i[0].name  # vLink name
                pl_name = i[1].name  # pLink name as (source,target)
                pl_reverse_name = i[1].reverse_name  # plink name as (target,source)
                decision_variable = vL[vl_name, pl_name]

                if vL[vl_name, pl_name].x == 1 or vL[vl_name, pl_reverse_name].x == 1:
                    is_pl_in_solution = True  # The physical link is selected in the new solution
                else:
                    is_pl_in_solution = False  # The physical link is not selected in the new solution

                if hosted_vlink_assign_dict[(vl_name, pl_name)] == 1 \
                        or hosted_vlink_assign_dict[(vl_name, pl_reverse_name)] == 1:
                    was_pl_in_old_assign = True  # The physical link was selected in the old assign
                else:
                    was_pl_in_old_assign = False  # The physical link was not selected in the old assign

                if is_pl_in_solution and not was_pl_in_old_assign:
                    # Add pl as a hosting link for the vl
                    vl.add_hosting_physical_link(pl)
                elif not is_pl_in_solution and was_pl_in_old_assign:
                    # Remove pl from being a hosting link for the vl
                    vl.remove_hosting_physical_link(pl)

        Logger.log.info(f"Assign new VMs...")
        for new_req in self._new_requests:
            new_req.is_allocated = True
            req_vnf_assignments = {}
            self.algorithm_result.requests_vnf_assignments_dict[new_req] = req_vnf_assignments
            new_req.vnf_allocation = req_vnf_assignments

            req_vlink_assignments = {}
            self.algorithm_result.requests_vlinks_assignments_dict[new_req] = req_vlink_assignments
            new_req.vlinks_allocation = req_vlink_assignments

            requested_vms_combinations = new_req.requested_vms_combinations
            x = new_req.new_vms_assign_vars
            requested_vms_dict = new_req.requested_vms_dict

            # Assign new VMs
            for v, s in requested_vms_combinations:
                vm = requested_vms_dict[v]
                server = net_node_dict[s]
                if x[v, s].x == 1:
                    if isinstance(vm, DummyVirtualMachine):
                        req_vnf_assignments[vm] = server
                        continue
                    if isinstance(server, Server):
                        server.add_virtual_machine(vm)
                        req_vnf_assignments[vm] = server
            self.algorithm_result.requests_vnf_assignments_dict[new_req] = req_vnf_assignments
            # Assign new vLinks
            requested_vlinks_objects_combination = new_req.requested_vlinks_object_combinations
            vL = new_req.new_vlinks_assign_vars
            for i in requested_vlinks_objects_combination:
                vl = i[0]  # vLink object
                pl = i[1]  # pLink object
                if vl not in req_vlink_assignments.keys():
                    req_vlink_assignments[vl] = []
                vl_name = i[0].name  # vLink name
                pl_name = i[1].name  # pLink name as (source,target)
                pl_reverse_name = i[1].reverse_name  # plink name as (target,source)
                if vL[vl_name, pl_name].x == 1 or vL[vl_name, pl_reverse_name].x == 1:
                    vl.add_hosting_physical_link(pl)
                    req_vlink_assignments[vl].append(pl)


class AlgorithmResult():

    def __init__(self) -> None:
        self._requests_vnf_assignments_dict = {}  # Maps requests to their vnf assignments dict
        self._requests_vlinks_assignments_dict = {}  # Maps requests to their vlinks assignments dict
        self._algorithm_name = None  # Heuristic used to solve the problem
        self._execution_time = None
        self._is_success = None  # Successful allocation
        self._cost = None

    @property
    def requests_vnf_assignments_dict(self):
        return self._requests_vnf_assignments_dict

    @requests_vnf_assignments_dict.setter
    def requests_vnf_assignments_dict(self, value):
        self._requests_vnf_assignments_dict = value

    @property
    def requests_vlinks_assignments_dict(self):
        return self._requests_vlinks_assignments_dict

    @requests_vlinks_assignments_dict.setter
    def requests_vlinks_assignments_dict(self, value):
        self._requests_vlinks_assignments_dict = value

    @property
    def algorithm_name(self):
        return self._algorithm_name

    @algorithm_name.setter
    def algorithm_name(self, value):
        self._algorithm_name = value

    @property
    def execution_time(self):
        return self._execution_time

    @execution_time.setter
    def execution_time(self, value):
        self._execution_time = value

    @property
    def is_success(self):
        return self._is_success

    @is_success.setter
    def is_success(self, value):
        self._is_success = value

    @property
    def cost(self):
        return self._cost

    @cost.setter
    def cost(self, value):
        self._cost = value

# TODO: implement AlgorithmResult
