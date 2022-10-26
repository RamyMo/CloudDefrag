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

import matplotlib.pyplot as plt
import networkx as nx

from CloudDefrag.Parsing.InputParser import InputParser
from CloudDefrag.Parsing.OutputParser import OutputParser
from CloudDefrag.Visualization.Visualizer import NetworkVisualizer, RequestVisualizer


def main():
    # Create the network
    net = PhysicalNetwork(name="Net1")
    # network_nodes_file = "input/RegionalTopo/01-NetworkNodes.csv"
    # network_connections_file = "input/RegionalTopo/02-NetworkConnections.csv"
    network_nodes_file = "input/ReducedTopo/01-NetworkNodes.csv"
    network_connections_file = "input/ReducedTopo/02-NetworkConnections.csv"
    input_parser = InputParser(net, network_nodes_file=network_nodes_file,
                               network_connections_file=network_connections_file)
    # Draw the network topology
    net_visual = NetworkVisualizer(net)
    net_visual.plot()

    number_of_iterations = 100
    average_repair_time_without_agent = 0
    success_ratio_without_agent = 0
    average_cost_without_agent = 0

    average_repair_time_with_agent = 0
    success_ratio_with_agent = 0
    average_cost_with_agent = 0

    for i in range(number_of_iterations):
        print(f"Iteration: {i}")
        seed = i + 1

        # Create the requests
        hosted_requests = input_parser.get_all_hosted_requests()
        # new_requests = input_parser.get_all_new_requests()
        new_requests, req_dist = input_parser.get_random_new_requests_from_gateway("w3",
                                                                         seed_number=seed)  # This bypass requests dist. file
        input_parser.assign_hosted_requests()

        # VNF Placement
        algo = RamyILP(net, new_requests, hosted_requests)
        algo.solve(display_result=True)

        if algo.isFeasible:
            algo.apply_result()
            out_parser = OutputParser(net, hosted_requests, new_requests)
            out_parser.parse_request_assignments()
        else:
            # Without Agent Recommendation
            inf_analyzer = InfeasAnalyzer(algo.model)
            # inf_analyzer.repair_infeas(all_constrs_are_modif=False)

            grouping_method = "Constraint_Type"  # "Resource_Location" or "Constraint_Type"

            inf_analyzer.repair_infeas(all_constrs_are_modif=False, constraints_grouping_method=grouping_method,
                                       recommeded_consts_groups_to_relax="[C1, C2, C3, C4]")

            repair_result = inf_analyzer.result
            average_repair_time_without_agent += repair_result.repair_exec_time
            average_cost_without_agent += repair_result.repair_cost
            if repair_result.is_repaired:
                success_ratio_without_agent += 1
            # repair_result.print_result()

            # With Agent Recommendation
            q_table = np.load(f"output/Q-tables/2000-qtable.npy")
            algo = RamyILP(net, new_requests, hosted_requests)
            inf_analyzer = InfeasAnalyzer(algo.model)
            recommended_constraints = "C2"
            current_state = [0, 0, 0, 0, 0, req_dist[0], req_dist[1], req_dist[2]]
            # for i in range(5):
            #     current_selection = np.argmax(q_table[tuple(current_state)])+1
            #     if current_selection == 6:
            #         break
            #     else:
            #         recommended_constraints += f" L{current_selection} "

            grouping_method = "Constraint_Type"  # "Resource_Location" or "Constraint_Type"
            inf_analyzer.repair_infeas(all_constrs_are_modif=False, constraints_grouping_method=grouping_method,
                                       recommeded_consts_groups_to_relax=recommended_constraints)

            repair_result = inf_analyzer.result
            average_repair_time_with_agent += repair_result.repair_exec_time
            if repair_result.is_repaired:
                success_ratio_with_agent += 1
                average_cost_with_agent += repair_result.repair_cost
            # repair_result.print_result()


    print("Done")
    average_repair_time_without_agent = average_repair_time_without_agent / number_of_iterations
    success_ratio_without_agent = (success_ratio_without_agent / number_of_iterations) * 100
    average_cost_without_agent = average_cost_without_agent / number_of_iterations

    average_repair_time_with_agent = average_repair_time_with_agent / success_ratio_with_agent
    average_cost_with_agent = average_cost_with_agent / success_ratio_with_agent
    success_ratio_with_agent = (success_ratio_with_agent / number_of_iterations) * 100


    print("\nRandom Test Result")
    print("\nWithout Agent:")
    print(f"Average Execution Time: {average_repair_time_without_agent}")
    print(f"Average Repair Cost: {average_cost_without_agent}")
    print(f"Success Ratio: {success_ratio_without_agent}")
    print("\nWith Agent")
    print(f"Average Execution Time: {average_repair_time_with_agent}")
    print(f"Average Repair Cost: {average_cost_with_agent}")
    print(f"Success Ratio: {success_ratio_with_agent}")


if __name__ == '__main__':
    main()
