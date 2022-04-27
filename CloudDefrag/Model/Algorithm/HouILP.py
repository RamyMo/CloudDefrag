from typing import List
import itertools
import gurobipy as gp
from CloudDefrag.Model.Graph import Network
from CloudDefrag.Model.Graph.Node import VirtualMachine


class HouILP:
    def __init__(self, net: Network, requests: List[VirtualMachine], **kwargs) -> None:
        model = gp.Model("HouILP")
        network = net
        requests = requests
        servers = net.servers
        servers_names = [server.node_name for server in net.servers]
        servers_dict = {server.node_name: server for server in net.servers}
        hosted_vms = kwargs["hosted_vms"] if "hosted_vms" in kwargs else []
        hosted_vms_names = [v.node_name for v in kwargs["hosted_vms"]] if "hosted_vms" in kwargs else []
        requested_vms_names = [v.node_name for v in requests]
        requested_vms_dict = {v.node_name: v for v in requests}
        hosted_vms_servers_assign_dict = {}  # Assignment of all existing VMs
        hosted_vms_servers_migrate_dict = {}  # Assignment of all existing VMs after VM migrations
        requested_vms_servers_assign_dict = {}  # Assignment of all new VMs requests
        requested_vms_servers_cost_dict = {}  # Assignment of all new VMs requests

        hosted_vms_servers_combination = list(itertools.product(hosted_vms, servers))
        for i in hosted_vms_servers_combination:
            if i[0].host_server == i[1]:
                hosted_vms_servers_assign_dict[(i[0].node_name, i[1].node_name)] = 1
                hosted_vms_servers_migrate_dict[(i[0].node_name, i[1].node_name)] = 1
            else:
                hosted_vms_servers_assign_dict[(i[0].node_name, i[1].node_name)] = 0
                hosted_vms_servers_migrate_dict[(i[0].node_name, i[1].node_name)] = 0
        del hosted_vms_servers_combination

        requested_vms_servers_combination = list(itertools.product(requests, servers))
        for i in requested_vms_servers_combination:
            requested_vms_servers_assign_dict[(i[0].node_name, i[1].node_name)] = 0
            requested_vms_servers_cost_dict[(i[0].node_name, i[1].node_name)] = 1
        del requested_vms_servers_combination

        requested_vms_combinations, requested_vms_servers_cost = \
            gp.multidict(requested_vms_servers_cost_dict)

        # Create decision variables for the model
        x = model.addVars(requested_vms_combinations, name="assign", vtype=gp.GRB.BINARY)

        # Objective: minimize total all new VMs assignments
        model.setObjective(x.prod(requested_vms_servers_cost), gp.GRB.MINIMIZE)

        # Resource Capacity Constraints
        # CPU Capacity Constraint
        server_cpu_constrs = model.addConstrs((gp.quicksum((x[v, s] * requested_vms_dict[v].specs.cpu) for v in
                                                           requested_vms_names) <= servers_dict[s].available_specs.cpu
                                               for s in servers_names), name='server_cpu_cap')

        server_mem_constrs = model.addConstrs((gp.quicksum((x[v, s] * requested_vms_dict[v].specs.memory) for v in
                                                           requested_vms_names) <=
                                               servers_dict[s].available_specs.memory
                                               for s in servers_names), name='server_memory_cap')

        server_storage_constrs = model.addConstrs((gp.quicksum((x[v, s] * requested_vms_dict[v].specs.storage) for v in
                                                           requested_vms_names) <=
                                               servers_dict[s].available_specs.storage
                                               for s in servers_names), name='server_storage_cap')
        # VM Single Host Constraints
        # Ensure that each VM is hosted by exactly one server
        vm_host_constrs = model.addConstrs((x.sum(v, '*') == 1 for v in requested_vms_names), name='vm_single_host')

        # Save model for inspection
        model.write('output/HouILP.lp')

        # Run optimization engine
        model.optimize()
