from copy import deepcopy
from typing import List
import itertools
import gurobipy as gp
import time

from CloudDefrag.Model.Algorithm.Algorithm import Algorithm
from CloudDefrag.Model.Algorithm.Heuristic import Heuristic
from CloudDefrag.Model.Algorithm.Request import VMRequest, NewVMRequest, HostedVMRequest
from CloudDefrag.Model.Graph import Network
from CloudDefrag.Model.Graph.Network import PhysicalNetwork
from CloudDefrag.Model.Graph.Node import VirtualMachine, Router, Server, DummyVirtualMachine
from CloudDefrag.Logging.Logger import Logger
import operator


class BinpackHeur(Heuristic):
    """
        BinpackHeur is a heuristic that bin pack vnfs at the nearest compute nodes
    """

    def __init__(self, net: PhysicalNetwork, new_requests: List[NewVMRequest], hosted_requests: List[HostedVMRequest],
                 **kwargs) \
            -> None:
        super().__init__(net, new_requests, hosted_requests, **kwargs)

        self.name = "BinpackHeur"

    def __solve_binpack_heur(self):
        for new_req in self._new_requests:
            req_vnf_assignments = {}
            req_vlink_assignments = {}
            added_vnf_constrs = []
            added_vlinks_constrs = []
            server_lengths = None
            failed_request_assign = False  # Equal true if heuristic fails to assign request (partial assign)

            # Assign vnfs
            for vlink in new_req.vm_net.get_links():
                if failed_request_assign:  # if failed_request_assign break from the current request
                    break
                source = vlink.source
                target = vlink.target
                # If source is dummy vnf
                if isinstance(source, DummyVirtualMachine):
                    # Assign dummy vnf to the gateway router
                    req_vnf_assignments[source] = new_req.gateway_router
                    var = new_req.new_vms_assign_vars[(source.node_name, new_req.gateway_router.node_name)]
                    self._model.addConstr(var == 1, name=f"{self.name}_req{new_req.request_id}_dummy_vnf")
                    self._model.update()
                    added_vnf_constrs.append(
                        self._model.getConstrByName(f"{self.name}_req{new_req.request_id}_dummy_vnf"))
                    # Assign the target to the nearest server
                    server_lengths = self.gateway_servers_lengths_dict[new_req.gateway_router]
                    # Assign target vnf
                    for s, delay in server_lengths.items():
                        can_host = s.can_server_host_vm(target)
                        req_vlink_delay = vlink.link_specs.propagation_delay
                        if req_vlink_delay < delay:
                            failed_request_assign = True
                            break
                        if can_host and req_vlink_delay >= delay:
                            var = new_req.new_vms_assign_vars[(target.node_name, s.node_name)]
                            s.add_virtual_machine(target)
                            req_vnf_assignments[target] = s
                            self._model.addConstr(var == 1,
                                                  name=f"{self.name}_req{new_req.request_id}_{target.node_name}")
                            self._model.update()
                            added_vnf_constrs.append(
                                self._model.getConstrByName(f"{self.name}_req{new_req.request_id}_{target.node_name}"))
                            break
                # If both source and target are assigned
                elif source in req_vnf_assignments.keys() and target in req_vnf_assignments.keys():
                    continue
                elif source in req_vnf_assignments.keys():
                    current_node = req_vnf_assignments[source]
                    server_lengths = self.servers_to_servers_sorted_lengths_dict[current_node]

                    for s, delay in server_lengths.items():
                        can_host = s.can_server_host_vm(target)
                        req_vlink_delay = vlink.link_specs.propagation_delay
                        if req_vlink_delay < delay:
                            failed_request_assign = True
                            break
                        if can_host and req_vlink_delay >= delay:
                            var = new_req.new_vms_assign_vars[(target.node_name, s.node_name)]
                            s.add_virtual_machine(target)
                            req_vnf_assignments[target] = s
                            self._model.addConstr(var == 1,
                                                  name=f"{self.name}_req{new_req.request_id}_{target.node_name}")
                            self._model.update()
                            added_vnf_constrs.append(self._model.getConstrByName(
                                f"{self.name}_req{new_req.request_id}_{target.node_name}"))
                            break
                    print("")

            # Make sure that all vnfs were assigned
            if any(vm not in req_vnf_assignments.keys() for vm in new_req.vm_net.get_vms()):
                failed_request_assign = True

            # If vnf failed_request_assign undo partial assignment.
            if failed_request_assign:
                for constr in added_vnf_constrs:
                    self._model.remove(constr)
                for vnf, server in req_vnf_assignments.items():
                    if isinstance(vnf, DummyVirtualMachine):
                        continue
                    else:
                        server.remove_virtual_machine(vnf)

            # If vnf assignment was done start assign vlinks
            if not failed_request_assign:
                for vlink in new_req.vm_net.get_links():
                    source_vnf = vlink.source
                    target_vnf = vlink.target
                    source_node = req_vnf_assignments[source_vnf]
                    target_node = req_vnf_assignments[target_vnf]
                    delay_req = vlink.link_specs.propagation_delay
                    bw_req = vlink.link_specs.bandwidth
                    shortest_physical_path = self.get_shorted_path_between_two_nodes_as_edges(source_node, target_node)
                    # Verify that shortest physical path meets req
                    provided_delay = 0
                    for pl in shortest_physical_path:
                        provided_delay += pl.link_specs.propagation_delay
                        if bw_req > pl.link_specs.bandwidth:
                            failed_request_assign = True
                    if provided_delay > delay_req:
                        failed_request_assign = True
                    # Stop if vlink assign fails
                    if failed_request_assign:
                        break

                    # Added constrs for vlinks decisions and apply change to physical links
                    for pl in shortest_physical_path:
                        vlink.add_hosting_physical_link(pl)  # Apply change to physical link
                        # Add constrs
                        # TODO: adding vlink decision constraints makes gurobi give infeasible solution (Investigate)
                        vl_var = new_req.new_vlinks_assign_vars[vlink.name, pl.name]
                        self._model.addConstr(vl_var == 1,
                                              name=f"{self.name}_req{new_req.request_id}_{vlink.name}")
                        self._model.update()
                        added_vlinks_constrs.append(
                            self._model.getConstrByName(f"{self.name}_req{new_req.request_id}_{vlink.name}"))

                    req_vlink_assignments[vlink] = shortest_physical_path

            # If vlink assign failed undo vnf and vlink partial assignment.
            if failed_request_assign:
                # undo vnf assign
                for constr in added_vnf_constrs:
                    self._model.remove(constr)
                for vnf, server in req_vnf_assignments.items():
                    if isinstance(vnf, DummyVirtualMachine):
                        continue
                    else:
                        server.remove_virtual_machine(vnf)
                # undo vlink assign
                for constr in added_vlinks_constrs:
                    self._model.remove(constr)
                for vlink, plink in req_vlink_assignments.items():
                    vlink.add_hosting_physical_link(plink)  # Undo applying change to physical link

            if failed_request_assign:
                self.heuristic_result.requests_vnf_assignments_dict[new_req] = None
                self.heuristic_result.requests_vlinks_assignments_dict[new_req] = None
            else:   # Successful Allocation
                self.heuristic_result.requests_vnf_assignments_dict[new_req] = req_vnf_assignments
                self.heuristic_result.requests_vlinks_assignments_dict[new_req] = req_vlink_assignments
                self.heuristic_result.is_success = True

        self.heuristic_result.heuristic_model = self.model
        self.heuristic_result.heuristic_name = self.name


    def solve(self, **kwargs):
        Logger.log.info(f"Solving problem model {self._model_name} using {self.name} Heuristic...")
        start_time = time.time()
        self.__solve_binpack_heur()
        execution_time = time.time() - start_time
        self.heuristic_result.execution_time = execution_time
        # Save model for inspection
        self._model.write(f'output/{self._model_name}_after_heru.lp')

        #TODO: fix why self._model.optimize() results in infeasible model for heuristic
        # self._model.optimize()
        #
        # if self.isFeasible:
        #     Logger.log.info(f"Model {self._model_name} is feasible")
        #     if kwargs["display_result"]:
        #         self.display_result()
        # else:
        #     Logger.log.info(f"Model {self._model_name} is infeasible")
        #     # print(f"Model {self._model_name} is infeasible")
