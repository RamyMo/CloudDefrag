#!/usr/bin/python3
# The main code of the Simulator
import networkx

from CloudDefrag.Model.Algorithm.ArisILP import ArisILP
from CloudDefrag.Model.Algorithm.BinpackHeur import BinpackHeur
from CloudDefrag.Model.Algorithm.RamyILP import RamyILP
from CloudDefrag.Model.Algorithm.Request import VMRequest, NewVMRequest, HostedVMRequest
from CloudDefrag.Model.Graph.Link import VirtualLink, LinkSpecs, PhysicalLink
from CloudDefrag.Model.Graph.Network import PhysicalNetwork, VirtualNetwork
from CloudDefrag.Model.Graph.Node import Server, VirtualMachine, Router, DummyVirtualMachine
from CloudDefrag.Model.Graph.Specs import Specs
from CloudDefrag.InfeasAnalysis.InfeasAnalysis import InfeasAnalyzer
import matplotlib.pyplot as plt
import networkx as nx

from CloudDefrag.Parsing.InputParser import InputParser
from CloudDefrag.Parsing.OutputParser import OutputParser
from CloudDefrag.Visualization.Visualizer import NetworkVisualizer, RequestVisualizer


# TODO: Improve Network Visualization

def main():
    # Input Parameters
    enable_infeas_repair = True
    make_random_new_requests = False
    algorithm_name = "RamyILP"

    # Create the network
    net, input_parser = create_network("Net1")

    # Draw the network topology
    net_visual = NetworkVisualizer(net)
    net_visual.plot()

    # Create the requests
    hosted_requests, new_requests = create_requests(input_parser, make_random_new_requests)

    # Apply the placement of the hosted requests (if any)
    input_parser.assign_hosted_requests()

    # VNF Placement
    # TODO: fix differences between objective functions of RamyILP and BinpackHeur

    algo = get_algorithm(net, new_requests, hosted_requests, algorithm_name)

    # Solve the formulated problem
    algo.solve(display_result=True)

    # Check Feasibility
    if algo.isFeasible:
        algo.apply_result()
        out_parser = OutputParser(net, hosted_requests, new_requests)
        out_parser.parse_request_assignments()
    elif enable_infeas_repair:
        # Repair Infeas
        inf_analyzer = InfeasAnalyzer(algo.model)
        grouping_method = "Resource_Location"  # "Resource_Location" or "Constraint_Type"
        recommended_constraints = "[L1, L2, L3, L4, L5]"
        #TODO: get recommended_constraints from the agent
        inf_analyzer.repair_infeas(all_constrs_are_modif=False, constraints_grouping_method=grouping_method,
                                   recommeded_consts_groups_to_relax=recommended_constraints)

        repair_result = inf_analyzer.result
        repair_result.print_result()

        # Apply repair and resolve
        if repair_result.is_repaired:
            inf_analyzer.apply_infeas_repair(net, hosted_requests, new_requests)
            new_algo = get_algorithm(net, new_requests, hosted_requests, algorithm_name)
            new_algo.solve(display_result=True)
            # Todo: when number of requests of type 2 exceeds 9:repair_result.is_repaired is true but new_algo.isFeasible is false
            if new_algo.isFeasible:
                algo.apply_result()
                out_parser = OutputParser(net, hosted_requests, new_requests)
                out_parser.parse_request_assignments()
    else:
        print("Model is Infeasible")
    net_visual.interactive_visual()
    print("Done")


def create_network(network_name):
    net = PhysicalNetwork(name=network_name)
    # network_nodes_file = "input/RegionalTopo/01-NetworkNodes.csv"
    # network_connections_file = "input/RegionalTopo/02-NetworkConnections.csv"
    network_nodes_file = "input/ReducedTopo/01-NetworkNodes.csv"
    network_connections_file = "input/ReducedTopo/02-NetworkConnections.csv"
    input_parser = InputParser(net, network_nodes_file=network_nodes_file,
                               network_connections_file=network_connections_file)
    return net, input_parser


def create_requests(input_parser, make_random_new_requests):
    # Todo: Generalize make_random_new_requests
    hosted_requests = input_parser.get_all_hosted_requests()
    if make_random_new_requests:
        new_requests, req_dist = input_parser.get_random_new_requests_from_gateway("w3",
                                                                                   seed_number=0)  # This bypass requests dist. file
    else:
        new_requests = input_parser.get_all_new_requests()
    return hosted_requests, new_requests


def get_algorithm(net, new_requests, hosted_requests, algorithm_name):
    """
    Returns algorithm instance of type selected based on algorithm_name.
    :param net: Network to be used
    :param new_requests: New requests to be assigned
    :param hosted_requests: Hosted requests in the network
    :param algorithm_name: The name of the algorithm. Supported algorithms: RamyILP, ArisILP, BinpackHeur
    :return: Return the algorithm selected based on algorithm_name
    """
    algo = None
    if algorithm_name == "RamyILP":
        algo = RamyILP(net, new_requests=new_requests, hosted_requests=hosted_requests)
    elif algorithm_name == "ArisILP":
        algo = ArisILP(net, new_requests=new_requests, hosted_requests=hosted_requests)
    elif algorithm_name == "BinpackHeur":
        algo = BinpackHeur(net, new_requests=new_requests, hosted_requests=hosted_requests)
    return algo


if __name__ == '__main__':
    main()
