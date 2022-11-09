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


def main():
    # Create the network
    net = PhysicalNetwork(name="Net1")
    network_nodes_file = "input/ReducedTopo/01-NetworkNodes.csv"
    network_connections_file = "input/ReducedTopo/02-NetworkConnections.csv"
    input_parser = InputParser(net, network_nodes_file=network_nodes_file,
                               network_connections_file=network_connections_file)

    # Feas Rest Dataset
    file_name_train = "output/Datasets/FeasRest_Train_Set1.CSV"
    file_name_test = "output/Datasets/FeasRest_Test_Set1.CSV"

    number_of_samples = 100

    with open(file_name_train, "w") as file:
        field_names = ["Class", "New Requests"]
        writer = csv.DictWriter(file, fieldnames=field_names)
        writer.writeheader()

        for i in range(number_of_samples):

            print(f"Iteration: {i}")
            seed = i + 1

            # Create the requests
            hosted_requests = input_parser.get_all_hosted_requests()
            # new_requests = input_parser.get_all_new_requests()
            new_requests, req_dist = input_parser.get_random_new_requests_from_gateway_type1("w3",
                                                                                       seed_number=seed)  # This bypass requests dist. file
            input_parser.assign_hosted_requests()

            # VNF Placement
            algo = RamyILP(net, new_requests, hosted_requests)
            algo.solve(display_result=True)
            print(f"Number of requests = {req_dist[0]}")
            if algo.isFeasible:
                algo.apply_result()
                out_parser = OutputParser(net, hosted_requests, new_requests)
                out_parser.parse_request_assignments()
            else:
                inf_analyzer = InfeasAnalyzer(algo.model)
                grouping_method = "Resource_Location"  # "Resource_Location" or "Constraint_Type"
                inf_analyzer.repair_infeas(all_constrs_are_modif=False, constraints_grouping_method=grouping_method,
                                           recommeded_consts_groups_to_relax="[L1, L2, L3, L4, L5]")
                repair_result = inf_analyzer.result
                selected_groups_without_agent = repair_result.selected_consts_groups_to_relax
                print(f"Selected constraints agent: {selected_groups_without_agent}")
                selection_class = get_selection_as_class(selected_groups=selected_groups_without_agent)

                writer.writerow({"Class": selection_class, "New Requests": req_dist[0]})

    with open(file_name_test, "w") as file:
        field_names = ["Class", "New Requests"]
        writer = csv.DictWriter(file, fieldnames=field_names)
        writer.writeheader()

        for i in range(number_of_samples):

            print(f"Iteration: {i}")
            seed = i + 1

            # Create the requests
            hosted_requests = input_parser.get_all_hosted_requests()
            # new_requests = input_parser.get_all_new_requests()
            new_requests, req_dist = input_parser.get_random_new_requests_from_gateway_type1("w3",
                                                                                       seed_number=seed)  # This bypass requests dist. file
            input_parser.assign_hosted_requests()

            # VNF Placement
            algo = RamyILP(net, new_requests, hosted_requests)
            algo.solve(display_result=True)
            print(f"Number of requests = {req_dist[0]}")
            if algo.isFeasible:
                algo.apply_result()
                out_parser = OutputParser(net, hosted_requests, new_requests)
                out_parser.parse_request_assignments()
            else:
                inf_analyzer = InfeasAnalyzer(algo.model)
                grouping_method = "Resource_Location"  # "Resource_Location" or "Constraint_Type"
                inf_analyzer.repair_infeas(all_constrs_are_modif=False, constraints_grouping_method=grouping_method,
                                           recommeded_consts_groups_to_relax="[L1, L2, L3, L4, L5]")
                repair_result = inf_analyzer.result
                selected_groups_without_agent = repair_result.selected_consts_groups_to_relax
                print(f"Selected constraints agent: {selected_groups_without_agent}")
                selection_class = get_selection_as_class(selected_groups=selected_groups_without_agent)

                writer.writerow({"Class": selection_class, "New Requests": req_dist[0]})


if __name__ == '__main__':
    main()


