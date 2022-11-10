#!/usr/bin/python3
# The main code of the Simulator
import networkx

from CloudDefrag.Model.Algorithm.RamyILP import RamyILP
from CloudDefrag.Model.Algorithm.Request import VMRequest, NewVMRequest, HostedVMRequest
from CloudDefrag.Model.Graph.Link import VirtualLink, LinkSpecs, PhysicalLink
from CloudDefrag.Model.Graph.Network import PhysicalNetwork, VirtualNetwork
from CloudDefrag.Model.Graph.Node import Server, VirtualMachine, Router, DummyVirtualMachine
from CloudDefrag.Model.Graph.Specs import Specs
from CloudDefrag.InfeasAnalysis.InfeasAnalysis import InfeasAnalyzer
from CloudDefrag.InfeasAnalysis.iis.RepairResult import RepairResult
import numpy as np
import csv
import re
import sys


import matplotlib.pyplot as plt
import networkx as nx

from CloudDefrag.Parsing.InputParser import InputParser
from CloudDefrag.Parsing.OutputParser import OutputParser
from CloudDefrag.Visualization.Visualizer import NetworkVisualizer, RequestVisualizer

def get_selection_as_class(selected_groups):
    selection_class = 0
    for group in selected_groups:
        power = int(re.search('L(.+?)', group).group(1)) - 1
        selection_class+= 2**power

    return selection_class


def create_row_dict(selection_class, req_dist, net):
    row_dict = {"Class": selection_class,
                "W2T1": req_dist["w2"][0], "W2T2": req_dist["w2"][1], "W2T3": req_dist["w2"][2],
                "W3T1": req_dist["w3"][0], "W3T2": req_dist["w3"][1], "W3T3": req_dist["w3"][2],
                "W4T1": req_dist["w4"][0], "W4T2": req_dist["w4"][1], "W4T3": req_dist["w4"][2],
                "W5T1": req_dist["w5"][0], "W5T2": req_dist["w5"][1], "W5T3": req_dist["w5"][2]}
    for s in net.get_servers():
        row_dict[s.node_name + "_cpu"] = s.available_specs.cpu
        row_dict[s.node_name + "_memory"] = s.available_specs.memory
        row_dict[s.node_name + "_disk"] = s.available_specs.storage

    for l in net.get_links():
        row_dict[l.name + "_bw"] = l.link_specs.available_bandwidth
        row_dict[l.name + "_delay"] = l.link_specs.propagation_delay
    return row_dict



def main():
    # Create the network
    net = PhysicalNetwork(name="Net1")
    network_nodes_file = "input/ReducedTopo/01-NetworkNodes.csv"
    network_connections_file = "input/ReducedTopo/02-NetworkConnections.csv"
    input_parser = InputParser(net, network_nodes_file=network_nodes_file,
                               network_connections_file=network_connections_file)

    is_train = True
    # if int(sys.argv[1]) == 1:
    #     is_train = True
    # else:
    #     is_train = False

    extend = False
    # if int(sys.argv[2]) == 1:
    #     extend = True
    # else:
    #     extend = False

    number_of_samples = 10

    # Feas Rest Dataset
    if is_train:
        file_name = "output/Datasets/FeasRest_Train_Set1.CSV"
    else:
        file_name = "output/Datasets/FeasRest_Test_Set1.CSV"


    field_names = ["Class", "W2T1", "W2T2", "W2T3", "W3T1", "W3T2", "W3T3", "W4T1", "W4T2", "W4T3",
                   "W5T1", "W5T2", "W5T3"]

    for s in net.get_servers():
        field_names.append(s.node_name + "_cpu")
        field_names.append(s.node_name + "_memory")
        field_names.append(s.node_name + "_disk")

    for l in net.get_links():
        field_names.append(l.name + "_bw")
        field_names.append(l.name + "_delay")

    if extend:
        with open(file_name, "a") as file:
            writer = csv.DictWriter(file, fieldnames=field_names)
            for i in range(number_of_samples):
                print(f"Iteration: {i}")
                # Create the requests
                hosted_requests = input_parser.get_all_hosted_requests()
                # new_requests = input_parser.get_all_new_requests()
                new_requests, req_dist = input_parser.get_random_new_requests_from_all_gateways()  # This bypass requests dist. file
                input_parser.assign_hosted_requests()

                # VNF Placement
                algo = RamyILP(net, new_requests, hosted_requests)
                algo.solve(display_result=False)
                if algo.isFeasible:
                    selection_class = 0
                    row_dict = create_row_dict(selection_class, req_dist, net)
                    writer.writerow(row_dict)
                else:
                    inf_analyzer = InfeasAnalyzer(algo.model)
                    grouping_method = "Resource_Location"  # "Resource_Location" or "Constraint_Type"
                    inf_analyzer.repair_infeas(all_constrs_are_modif=False, constraints_grouping_method=grouping_method,
                                               recommeded_consts_groups_to_relax="[L1, L2, L3, L4, L5]")
                    repair_result = inf_analyzer.result
                    selected_groups_without_agent = repair_result.selected_consts_groups_to_relax
                    print(f"Selected constraints agent: {selected_groups_without_agent}")
                    selection_class = get_selection_as_class(selected_groups=selected_groups_without_agent)
                    row_dict = create_row_dict(selection_class, req_dist, net)
                    writer.writerow(row_dict)

                # Garbage Collection
                algo.model.dispose()
                algo.model = None
                algo.model = None
                for req in new_requests:
                    req.new_vms_assign_vars = None
                    req.new_vlinks_assign_vars = None
                    req.requested_vlink_revenue_dict = None
                    req.requested_vlink_prop_delay_dict = None
                    req.requested_vlink_cost_dict = None
                    req.requested_vlink_assign_dict = None
                    req.requested_vlinks_prop_delay = None
                    req.requested_vlinks_revenue = None
                    req.requested_vlinks_combinations = None
                    req.requested_vms_combinations = None
                    req.requested_vlinks_cost = None
                    req.requested_vms_servers_assign_dict = None
                    req.requested_vms_servers_cost_dict = None
                    req.requested_vms_servers_revenue_dict = None
                    req = None
    else:
        with open(file_name, "w") as file:
            writer = csv.DictWriter(file, fieldnames=field_names)
            writer.writeheader()
            for i in range(number_of_samples):
                print(f"Iteration: {i}")
                # Create the requests
                hosted_requests = input_parser.get_all_hosted_requests()
                # new_requests = input_parser.get_all_new_requests()
                new_requests, req_dist = input_parser.get_random_new_requests_from_all_gateways()  # This bypass requests dist. file
                input_parser.assign_hosted_requests()

                # VNF Placement
                algo = RamyILP(net, new_requests, hosted_requests)
                algo.solve(display_result=True)
                if algo.isFeasible:
                    selection_class = 0
                    row_dict = create_row_dict(selection_class, req_dist, net)
                    writer.writerow(row_dict)
                else:
                    inf_analyzer = InfeasAnalyzer(algo.model)
                    grouping_method = "Resource_Location"  # "Resource_Location" or "Constraint_Type"
                    inf_analyzer.repair_infeas(all_constrs_are_modif=False, constraints_grouping_method=grouping_method,
                                               recommeded_consts_groups_to_relax="[L1, L2, L3, L4, L5]")
                    repair_result = inf_analyzer.result
                    selected_groups_without_agent = repair_result.selected_consts_groups_to_relax
                    print(f"Selected constraints agent: {selected_groups_without_agent}")
                    selection_class = get_selection_as_class(selected_groups=selected_groups_without_agent)
                    row_dict = create_row_dict(selection_class, req_dist, net)
                    writer.writerow(row_dict)

                # Garbage Collection
                algo.model.dispose()
                algo.model = None
                algo.model = None
                for req in new_requests:
                    req.new_vms_assign_vars = None
                    req.new_vlinks_assign_vars = None
                    req.requested_vlink_revenue_dict = None
                    req.requested_vlink_prop_delay_dict = None
                    req.requested_vlink_cost_dict = None
                    req.requested_vlink_assign_dict = None
                    req.requested_vlinks_prop_delay = None
                    req.requested_vlinks_revenue = None
                    req.requested_vlinks_combinations = None
                    req.requested_vms_combinations = None
                    req.requested_vlinks_cost = None
                    req.requested_vms_servers_assign_dict = None
                    req.requested_vms_servers_cost_dict = None
                    req.requested_vms_servers_revenue_dict = None
                    req = None








def garbage_collector(model, algo, new_requests):
    model.dispose()
    model = None
    algo = None
    # gp.disposeDefaultEnv()
    for req in new_requests:
        req.new_vms_assign_vars = None
        req.new_vlinks_assign_vars = None
        req.requested_vlink_revenue_dict = None
        req.requested_vlink_prop_delay_dict = None
        req.requested_vlink_cost_dict = None
        req.requested_vlink_assign_dict = None
        req.requested_vlinks_prop_delay = None
        req.requested_vlinks_revenue = None
        req.requested_vlinks_combinations = None
        req.requested_vms_combinations = None
        req.requested_vlinks_cost = None
        req.requested_vms_servers_assign_dict = None
        req.requested_vms_servers_cost_dict = None
        req.requested_vms_servers_revenue_dict = None
        req = None






if __name__ == '__main__':
    main()


