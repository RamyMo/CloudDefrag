from typing import List
import itertools
import gurobipy as gp

from CloudDefrag.Model.Algorithm.Request import VMRequest, NewVMRequest, HostedVMRequest
from CloudDefrag.Model.Graph import Network
from CloudDefrag.Model.Graph.Network import PhysicalNetwork
from CloudDefrag.Model.Graph.Node import VirtualMachine, Router, Server, DummyVirtualMachine
from CloudDefrag.Logging.Logger import Logger


class RamyILP:
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

        Logger.log.info(f"Created an instance of RamyILP algorithm for model {self._model_name}.")
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
        # Ensure that servers are not overused
        self.__create_servers_resource_capacity_constrs()

        # Links B.W Capacity Constraints
        # Ensure that Links B.W are not overused
        self.__create_links_bw_capacity_constrs()

        # Links Prop. Delay Constraints
        # Ensure that Links Links Prop. Delay are respected
        self.__create_prop_delay_constrs()

        # E2E delay constrs
        # Ensure that the E2E delay requirement is met
        self.__create_e2e_delay_constrs()

        # TODO: Add server processing delay constraints

        # Flow conservation constraint
        # Verifies that there will be a virtual link between each two consecutive VMs hosted on two different servers.
        self.__create_flow_conservation_constr()

        # VM Single Host Constraints
        # Ensure that each VM is hosted by exactly one node
        self.__create_single_host_constrs()

        # VM Single Server Constraints
        # Ensure that each VM is hosted by exactly one server
        self.__create_single_server_constrs()

        # Ensure that dummy vms are placed only at their gateway routers
        self.__create_dummy_vm_constrs()

    def __create_decision_variables(self):
        # New VMs Assignment variables
        for new_req in self._new_requests:
            new_req.new_vms_assign_vars = self._model.addVars(new_req.requested_vms_combinations,
                                                              name=f"new_assign", vtype=gp.GRB.BINARY)
            new_req.new_vlinks_assign_vars = self._model.addVars(new_req.requested_vlinks_combinations,
                                                                 name=f"new_assign", vtype=gp.GRB.BINARY)

        # Hosted VMs Assignment variables after migration
        for hosted_req in self._hosted_requests:
            hosted_req.hosted_vms_assign_vars = self._model.addVars(hosted_req.hosted_vms_combinations,
                                                                    name=f"hosted_assign", vtype=gp.GRB.BINARY)
            hosted_req.hosted_vlinks_assign_vars = self._model.addVars(hosted_req.hosted_vlinks_combinations,
                                                                       name=f"hosted_assign", vtype=gp.GRB.BINARY)

    def __create_objective_function(self):
        # Revenue PI
        revenue = 0
        for new_req in self._new_requests:
            revenue += new_req.new_vms_assign_vars.prod(new_req.requested_vms_servers_revenue)

        # Cost Kappa
        cost = 0
        # vm_migration_cost and vlink_migration_cost
        for hosted_req in self._hosted_requests:
            # vm_migration_cost
            vm_assign_dict = hosted_req.hosted_vms_servers_assign_dict
            y = hosted_req.hosted_vms_assign_vars
            vms_dict = hosted_req.hosted_vms_dict
            vms_combinations = hosted_req.hosted_vms_combinations
            vm_migration_cost = gp.quicksum((vm_assign_dict[v, s] * (1 - y[v, s])) *
                                            vms_dict[v].vm_migration_coeff for v, s in vms_combinations)

            # vlink_migration_cost
            vlink_assign_dict = hosted_req.hosted_vlink_assign_dict
            vl = hosted_req.hosted_vlinks_assign_vars
            vlinks_dict = hosted_req.hosted_vlinks_dict
            vlink_migrate_cost_dict = hosted_req.hosted_vlink_migrate_cost_dict
            vlinks_combination = hosted_req.hosted_vlinks_combinations
            vlink_migration_cost = gp.quicksum((vlink_assign_dict[v, s] * (1 - vl[v, s])) *
                                               vlink_migrate_cost_dict[v, s] for v, s in vlinks_combination)
            self._model.update()
            cost += vm_migration_cost + vlink_migration_cost
            #TODO: Add hosted vlink assign cost
        # New vlinks assign cost
        for new_req in self._new_requests:
            new_vlinks_assign_cost = new_req.new_vlinks_assign_vars.prod(new_req.requested_vlinks_cost)
            cost += new_vlinks_assign_cost

        self._model.setObjective(revenue - cost, gp.GRB.MAXIMIZE)

    def __create_servers_resource_capacity_constrs(self):
        # Resource Capacity Constraints: CPU, Memory & Storage
        for s in self._servers_names:
            # New requests terms
            new_requests_cpu_req_term = 0
            new_requests_memory_req_term = 0
            new_requests_storage_req_term = 0
            for new_req in self._new_requests:
                x = new_req.new_vms_assign_vars
                requested_vms_dict = new_req.requested_vms_dict
                requested_vms_names = new_req.requested_vms_names

                new_requests_cpu_req_term += gp.quicksum((x[v, s] * requested_vms_dict[v].specs.cpu) for v in
                                                         requested_vms_names)
                new_requests_memory_req_term += gp.quicksum((x[v, s] * requested_vms_dict[v].specs.memory) for v in
                                                            requested_vms_names)
                new_requests_storage_req_term += gp.quicksum((x[v, s] * requested_vms_dict[v].specs.storage) for v in
                                                             requested_vms_names)

            # Hosted requests terms
            hosted_requests_cpu_req_term = 0
            hosted_requests_memory_req_term = 0
            hosted_requests_storage_req_term = 0
            for hosted_req in self._hosted_requests:
                y = hosted_req.hosted_vms_assign_vars
                hosted_vms_dict = hosted_req.hosted_vms_dict
                hosted_vms_names = hosted_req.hosted_vms_names
                hosted_requests_cpu_req_term += gp.quicksum((y[v, s] * hosted_vms_dict[v].specs.cpu) for v in
                                                            hosted_vms_names)
                hosted_requests_memory_req_term += gp.quicksum((y[v, s] * hosted_vms_dict[v].specs.memory) for v in
                                                               hosted_vms_names)
                hosted_requests_storage_req_term += gp.quicksum((y[v, s] * hosted_vms_dict[v].specs.storage) for v in
                                                                hosted_vms_names)

            self._servers_dict[s].server_cpu_constrs = self._model.addConstr(
                (hosted_requests_cpu_req_term + new_requests_cpu_req_term <= self._servers_dict[s].specs.cpu),
                name=f"{self._servers_dict[s].node_name}_cpu_cap")

            self._servers_dict[s].server_memory_constrs = self._model.addConstr(
                (hosted_requests_memory_req_term + new_requests_memory_req_term <= self._servers_dict[s].specs.memory),
                name=f"{self._servers_dict[s].node_name}_memory_cap")

            self._servers_dict[s].server_storage_constrs = self._model.addConstr(
                (hosted_requests_storage_req_term + new_requests_storage_req_term <=
                 self._servers_dict[s].specs.storage), name=f"{self._servers_dict[s].node_name}_storage_cap")

    def __create_links_bw_capacity_constrs(self):
        for link in self._physical_links:
            plink1 = link.name
            plink2 = link.reverse_name
            # New requests terms
            new_requests_bw_req_term = 0
            for new_req in self._new_requests:
                vlink_vars = new_req.new_vlinks_assign_vars
                requested_vlinks_dict = new_req.requested_vlinks_dict
                requested_vlinks_names = new_req.requested_vlinks_names
                new_requests_bw_req_term += gp.quicksum(((vlink_vars[v, plink1] + vlink_vars[v, plink2]) *
                                                         requested_vlinks_dict[v].link_specs.bandwidth) for v in
                                                        requested_vlinks_names)
            # Hosted requests terms
            hosted_requests_bw_req_term = 0
            for hosted_req in self._hosted_requests:
                vlink_vars = hosted_req.hosted_vlinks_assign_vars
                hosted_vlinks_dict = hosted_req.hosted_vlinks_dict
                hosted_vlinks_names = hosted_req.hosted_vlinks_names
                hosted_requests_bw_req_term += gp.quicksum(((vlink_vars[v, plink1] + vlink_vars[v, plink2]) *
                                                            hosted_vlinks_dict[v].link_specs.bandwidth) for v in
                                                           hosted_vlinks_names)

            link.bw_constrs = self._model.addConstr((new_requests_bw_req_term + hosted_requests_bw_req_term) <=
                                                    link.link_specs.bandwidth, name=f"{link.name}_bw_cap")

    def __create_e2e_delay_constrs(self):
        # TODO: Add the processing delay and other kind of delays in the e2e constr.
        for new_req in self._new_requests:
            e2e_delay_req = new_req.e2e_delay
            link_vars = new_req.new_vlinks_assign_vars
            vlink_prop_delay_term = link_vars.prod(new_req.requested_vlinks_prop_delay)
            new_req.e2e_delay_constr = self._model.addConstr(vlink_prop_delay_term <= e2e_delay_req,
                                                             name=f"new_req{new_req.request_id}_e2e_delay")

        for hosted_req in self._hosted_requests:
            e2e_delay_req = hosted_req.e2e_delay
            link_vars = hosted_req.hosted_vlinks_assign_vars
            vlink_prop_delay_term = link_vars.prod(hosted_req.hosted_vlinks_prop_delay)
            hosted_req.e2e_delay_constr = self._model.addConstr(vlink_prop_delay_term <= e2e_delay_req,
                                                                name=f"hosted_req{hosted_req.request_id}_e2e_delay")

    def __create_prop_delay_constrs(self):
        plinks_dict = self._physical_links_dict
        for new_req in self._new_requests:
            link_vars = new_req.new_vlinks_assign_vars
            vlinks_dict = new_req.requested_vlinks_dict
            for vlink in new_req.requested_vlinks_names:
                req_prop_delay = vlinks_dict[vlink].link_specs.propagation_delay
                vlink_prop_delay_req_term = gp.quicksum(((link_vars[vlink, plink.name] +
                                                          link_vars[vlink, plink.reverse_name]) *
                                                         plink.link_specs.propagation_delay) for plink in
                                                        self._physical_links)
                vlinks_dict[vlink].prop_delay_req_constr = \
                    self._model.addConstr(vlink_prop_delay_req_term <= req_prop_delay, name=f"new_vlink_{vlink}"
                                                                                            f"_prop_delay")

        for hosted_req in self._hosted_requests:
            link_vars = hosted_req.hosted_vlinks_assign_vars
            vlinks_dict = hosted_req.hosted_vlinks_dict
            for vlink in hosted_req.hosted_vlinks_names:
                req_prop_delay = vlinks_dict[vlink].link_specs.propagation_delay
                vlink_prop_delay_req_term = gp.quicksum(((link_vars[vlink, plink.name] +
                                                          link_vars[vlink, plink.reverse_name]) *
                                                         plink.link_specs.propagation_delay) for plink
                                                        in self._physical_links)
                vlinks_dict[vlink].prop_delay_req_constr = \
                    self._model.addConstr(vlink_prop_delay_req_term <= req_prop_delay, name=f"hosted_vlink_{vlink}"
                                                                                            f"_prop_delay")

    def __create_flow_conservation_constr(self):

        nodes = self._nodes
        nodes_names = self._nodes_names
        nodes_dict = self._nodes_dict

        for new_req in self._new_requests:
            link_vars = new_req.new_vlinks_assign_vars
            vlinks_dict = new_req.requested_vlinks_dict
            vm_vars = new_req.new_vms_assign_vars
            vm_dict = new_req.requested_vms_dict
            for vlink in new_req.requested_vlinks_names:
                source = vlinks_dict[vlink].source
                target = vlinks_dict[vlink].target
                for u in nodes_names:
                    rhs = vm_vars[source.node_name, u] - vm_vars[target.node_name, u]
                    lhs = 0
                    for v in nodes_names:
                        if u == v:
                            continue
                        else:
                            if self._network.has_edge(nodes_dict[u], nodes_dict[v]):
                                var1 = f"({source.node_name},{target.node_name})", f"({u},{v})"
                                var2 = f"({source.node_name},{target.node_name})", f"({v},{u})"
                                lhs += link_vars[var1] - link_vars[var2]
                    self._model.addConstr(lhs == rhs, name=f"flow_cons_{vlink}_{u}")

        for hosted_req in self._hosted_requests:
            link_vars = hosted_req.hosted_vlinks_assign_vars
            vlinks_dict = hosted_req.hosted_vlinks_dict
            vm_vars = hosted_req.hosted_vms_assign_vars
            for vlink in hosted_req.hosted_vlinks_names:
                source = vlinks_dict[vlink].source
                target = vlinks_dict[vlink].target
                for u in nodes_names:
                    rhs = vm_vars[source.node_name, u] - vm_vars[target.node_name, u]
                    lhs = 0
                    for v in nodes_names:
                        if u == v:
                            continue
                        else:
                            if self._network.has_edge(nodes_dict[u], nodes_dict[v]):
                                var1 = f"({source.node_name},{target.node_name})", f"({u},{v})"
                                var2 = f"({source.node_name},{target.node_name})", f"({v},{u})"
                                lhs += link_vars[var1] - link_vars[var2]
                    self._model.addConstr(lhs == rhs, name=f"flow_cons_{vlink}_{u}")

    def __create_single_host_constrs(self):
        for new_req in self._new_requests:
            x = new_req.new_vms_assign_vars
            requested_vms_names = new_req.requested_vms_names
            self._model.addConstrs((x.sum(v, '*') <= 1 for v in requested_vms_names)
                                   , name='requested_vm_single_host')

        for hosted_req in self._hosted_requests:
            y = hosted_req.hosted_vms_assign_vars
            hosted_vms_names = hosted_req.hosted_vms_names
            self._model.addConstrs((y.sum(v, '*') == 1 for v in hosted_vms_names)
                                   , name='hosted_vm_single_host')

    def __create_single_server_constrs(self):
        server_names = self._servers_names
        for new_req in self._new_requests:
            vars = new_req.new_vms_assign_vars
            vms = new_req.vm_net.get_vms_except_dummy()
            vms_names = [vm.node_name for vm in vms]
            for vm in vms_names:
                term = gp.quicksum(vars[vm, s] for s in server_names)
                self._model.addConstr(term == 1, name=f'requested_vm_single_server[{vm}]')

        for hosted_req in self._hosted_requests:
            vars = hosted_req.hosted_vms_assign_vars
            vms = hosted_req.vm_net.get_vms_except_dummy()
            vms_names = [vm.node_name for vm in vms]
            for vm in vms_names:
                term = gp.quicksum(vars[vm, s] for s in server_names)
                self._model.addConstr(term == 1, name=f'hosted_vm_single_server[{vm}]')

    def __create_dummy_vm_constrs(self):
        for new_req in self._new_requests:
            vars = new_req.new_vms_assign_vars
            gateway_router = new_req.gateway_router
            dummy_vm = new_req.vm_net.get_dummy_vm()
            dummy_var = vars[dummy_vm.node_name, gateway_router.node_name]
            self._model.addConstr(dummy_var == 1, name=f"req{new_req.request_id}_dummy_vm")

        for hosted_req in self._hosted_requests:
            vars = hosted_req.hosted_vms_assign_vars
            gateway_router = hosted_req.gateway_router
            dummy_vm = hosted_req.vm_net.get_dummy_vm()
            dummy_var = vars[dummy_vm.node_name, gateway_router.node_name]
            self._model.addConstr(dummy_var == 1, name=f"req{hosted_req.request_id}_dummy_vm")

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
        Logger.log.info(f"Solving problem model {self._model_name} using RamyILP...")
        if kwargs["display_result"]:
            self.display_result()

    def display_result(self):
        # Model properties:
        print(f"Number of Decision Variables: {len(self._model.getVars())}")
        print(f"Number of Constraints: {len(self._model.getConstrs())}")
        # Display optimal values of decision variables
        print("\nDecision Variables:")
        for v in self._model.getVars():
            if v.x > 1e-6:
                print(f"{v.varName} = {v.x}")
        # Display optimal total matching score
        print('\nTotal cost: ', self._model.objVal)
        print(f"Runtime: {self._model.getAttr(gp.GRB.Attr.Runtime)} seconds")

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
                    is_pl_in_solution = True    # The physical link is selected in the new solution
                else:
                    is_pl_in_solution = False   # The physical link is not selected in the new solution

                if hosted_vlink_assign_dict[(vl_name, pl_name)] == 1 \
                        or hosted_vlink_assign_dict[(vl_name, pl_reverse_name)] == 1:
                    was_pl_in_old_assign = True     # The physical link was selected in the old assign
                else:
                    was_pl_in_old_assign = False    # The physical link was not selected in the old assign

                if is_pl_in_solution and not was_pl_in_old_assign:
                    # Add pl as a hosting link for the vl
                    vl.add_hosting_physical_link(pl)
                elif not is_pl_in_solution and was_pl_in_old_assign:
                    # Remove pl from being a hosting link for the vl
                    vl.remove_hosting_physical_link(pl)

        Logger.log.info(f"Assign new VMs...")
        for new_req in self._new_requests:
            requested_vms_combinations = new_req.requested_vms_combinations
            x = new_req.new_vms_assign_vars
            requested_vms_dict = new_req.requested_vms_dict

            # Assign new VMs
            for v, s in requested_vms_combinations:
                vm = requested_vms_dict[v]
                server = net_node_dict[s]
                if isinstance(vm, DummyVirtualMachine):
                    continue
                if x[v, s].x == 1:
                    if isinstance(server, Server):
                        server.add_virtual_machine(vm)

            # Assign new vLinks
            requested_vlinks_objects_combination = new_req.requested_vlinks_object_combinations
            vL = new_req.new_vlinks_assign_vars
            for i in requested_vlinks_objects_combination:
                vl = i[0]  # vLink object
                pl = i[1]  # pLink object
                vl_name = i[0].name  # vLink name
                pl_name = i[1].name  # pLink name as (source,target)
                pl_reverse_name = i[1].reverse_name  # plink name as (target,source)
                if vL[vl_name, pl_name].x == 1 or vL[vl_name, pl_reverse_name].x == 1:
                    vl.add_hosting_physical_link(pl)


