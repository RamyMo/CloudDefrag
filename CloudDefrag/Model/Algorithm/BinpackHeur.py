from copy import deepcopy
from typing import List
import itertools
import gurobipy as gp

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

        self.name="BinpackHeur"

    def __solve_binpack_heur(self):
        # TODO: Implement selection mechanism for the binpack
        assignments = {}
        for new_req in self._new_requests:
            server_lengths= None
            for vlink in new_req.vm_net.get_links():
                source = vlink.source
                target = vlink.target
                # If source is dummy vnf
                if isinstance(source, DummyVirtualMachine):
                    # Assign dummy vnf to the gateway router
                    assignments[source] = new_req.gateway_router.node_name
                    var = new_req.new_vms_assign_vars[(source.node_name, new_req.gateway_router.node_name)]
                    self._model.addConstr(var == 1, name=f"{self.name}_req{new_req.request_id}_dummy_vnf")
                    # Assign the target to the nearest server
                    server_lengths = self.gateway_servers_lengths_dict[new_req.gateway_router]
                    # Assign target vnf
                    for s, delay in server_lengths.items():
                        can_host = s.can_server_host_vm(target)
                        req_vlink_delay = vlink.link_specs.propagation_delay
                        if can_host and req_vlink_delay >= delay:
                            var = new_req.new_vms_assign_vars[(target.node_name, s.node_name)]
                            s.add_virtual_machine(target)
                            assignments[target] = s
                            self._model.addConstr(var == 1, name=f"{self.name}_req{new_req.request_id}_{target.node_name}")
                            break
                elif source in assignments.keys() and target in assignments.keys():
                    # TODO: for request of type 2, the placement of the last vnf needs to be verified to satsify requirments of vlink 3 to 4
                    continue
                elif source in assignments.keys():
                    current_node = assignments[source]
                    server_lengths = self.servers_to_servers_sorted_lengths_dict[current_node]

                    for s, delay in server_lengths.items():
                        can_host = s.can_server_host_vm(target)
                        req_vlink_delay = vlink.link_specs.propagation_delay
                        if can_host and req_vlink_delay >= delay:
                            var = new_req.new_vms_assign_vars[(target.node_name, s.node_name)]
                            s.add_virtual_machine(target)
                            assignments[target] = s
                            self._model.addConstr(var == 1, name=f"{self.name}_req{new_req.request_id}_{target.node_name}")
                            break
                    print("")

            # for vnf in new_req.vm_net.get_vms():
            #     # If dummy vnf
            #     if isinstance(vnf, DummyVirtualMachine):
            #         var = new_req.new_vms_assign_vars[(vnf.node_name,gateway_router.node_name)]
            #         self._model.addConstr(var == 1, name=f"{self.name}_req{req_id}_dummy_vnf")
            #     elif current_node == gateway_router:
            #
            #         for s, delay in server_lengths:
            #             pass
            #         print("")





            # TODO: Translate heuristic solution to fixing decision variables by adding constraints
            print("")


    def solve(self, **kwargs):
        Logger.log.info(f"Solving problem model {self._model_name} using Binpack Heuristic...")
        self.__solve_binpack_heur()
        # Save model for inspection
        self._model.write(f'output/{self._model_name}_after_heru.lp')
        self._model.optimize()
        if self.isFeasible:
            Logger.log.info(f"Model {self._model_name} is feasible")
            if kwargs["display_result"]:
                self.display_result()
        else:
            Logger.log.info(f"Model {self._model_name} is infeasible")
            # print(f"Model {self._model_name} is infeasible")
