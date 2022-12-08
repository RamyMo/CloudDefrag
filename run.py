#!/usr/bin/python3
# The main code of the Simulator
import re

import networkx
import numpy as np
import torch

from CloudDefrag.DQN.Agent import Agent
from CloudDefrag.DQN.Agent import train
from CloudDefrag.DQN.Model import Linear_QNet
from CloudDefrag.Model.Algorithm.Algorithm import Algorithm
from CloudDefrag.Model.Algorithm.ArisILP import ArisILP
from CloudDefrag.Model.Algorithm.BinpackHeur import BinpackHeur
from CloudDefrag.Model.Algorithm.Heuristic import Heuristic
from CloudDefrag.Model.Algorithm.RamyILP import RamyILP
from CloudDefrag.Model.Algorithm.Request import VMRequest, NewVMRequest, HostedVMRequest
from CloudDefrag.Model.Algorithm.SpreadHeur import SpreadHeur
from CloudDefrag.Model.Graph.Link import VirtualLink, LinkSpecs, PhysicalLink
from CloudDefrag.Model.Graph.Network import PhysicalNetwork, VirtualNetwork
from CloudDefrag.Model.Graph.Node import Server, VirtualMachine, Router, DummyVirtualMachine
from CloudDefrag.Model.Graph.Specs import Specs
from CloudDefrag.InfeasAnalysis.InfeasAnalysis import InfeasAnalyzer
import matplotlib.pyplot as plt
import networkx as nx
from CloudDefrag.DQN.Env import Env

from CloudDefrag.Parsing.InputParser import InputParser
from CloudDefrag.Parsing.OutputParser import OutputParser
from CloudDefrag.Simulator.Simulator import Simulator
from CloudDefrag.Visualization.Visualizer import NetworkVisualizer, RequestVisualizer


# TODO: Improve Network Visualization
# max_hops_for_connectivity tau


def main():
    max_hops_for_connectivity = 2
    # #Test DQN Env
    game = Env(max_hops_for_connectivity=max_hops_for_connectivity)
    agent = Agent(game)
    train(game, agent)
    # print("Done Training")

    # Load Model
    # trained_model_folder_path = './output/DQN/model/model.pth'
    # trained_model = Linear_QNet(game.state_vector_size, 256, game.action_space_size)
    # trained_model.load_state_dict(torch.load(trained_model_folder_path))
    # test_dqn_model(trained_model, max_hops_for_connectivity)





    # my_sim = Simulator(number_of_requests=50)
    # my_sim.algorithm_name = "BinpackHeur"  # RamyILP, BinpackHeur, SpreadHeur, ArisILP
    # my_sim.start()
    # my_sim.result.print_simulation_result()


    # # Input Parameters
    # make_random_new_requests = False
    # algorithm_name = "RamyILP" # RamyILP, BinpackHeur, SpreadHeur, ArisILP
    # network_topology = "Reduced"  # "Reduced" or "Regional"
    #
    # # Request parameters
    # single_request_allocation = True
    #
    # # Feasibility Restoration Parameters
    # enable_infeas_repair = False
    # grouping_method = "Resource_Location"  # "Resource_Location" or "Resource_Location"
    # compute_resource_factor = 500
    # bw_factor = 40
    # e2e_delay_factor = 5
    # propg_delay_factor = 10
    #
    #
    # # Create the network
    # net, input_parser = create_network("Net1", network_topology)
    #
    # # Draw the network topology
    # net_visual = NetworkVisualizer(net)
    # net_visual.plot()
    #
    #
    #
    #
    # for i in range(1):
    #     # Create the requests
    #     hosted_requests, new_requests = create_requests(input_parser, make_random_new_requests)
    #
    #     # Apply the placement of the hosted requests (if any)
    #     input_parser.assign_hosted_requests()
    #
    #     # VNF Placement
    #     # TODO: fix differences between objective functions of RamyILP and BinpackHeur
    #
    #     algo = get_algorithm(net, new_requests, hosted_requests, algorithm_name)
    #
    #     # Solve the formulated problem
    #     algo.solve(display_result=True, print_decision_variables=True)
    #
    #     if isinstance(algo, Heuristic):
    #         heuristic_result = algo.heuristic_result
    #         if heuristic_result.is_success:
    #             algo.display_result()
    #             out_parser = OutputParser(net, hosted_requests, new_requests)
    #             out_parser.parse_request_assignments()
    #
    #     elif isinstance(algo, Algorithm):
    #         # Check Feasibility
    #         if algo.isFeasible:
    #             algo.apply_result()
    #             out_parser = OutputParser(net, hosted_requests, new_requests)
    #             out_parser.parse_request_assignments()
    #         elif enable_infeas_repair:
    #             feasibility_restoration(algorithm_instance=algo, grouping_method=grouping_method,
    #                                     algorithm_name=algorithm_name,
    #                                     net=net, hosted_requests=hosted_requests, new_requests=new_requests,
    #                                     compute_resource_factor=compute_resource_factor, bw_factor=bw_factor,
    #                                     e2e_delay_factor=e2e_delay_factor, propg_delay_factor=propg_delay_factor)
    #         else:
    #             print("Model is Infeasible")
    #
    #     net_visual.interactive_visual()
    #
    #     print("Done")
    #
    #     new_requests[0].deallocate()
    #
    #     net_visual.interactive_visual()


def create_network(network_name, network_topology, max_hops_for_connectivity):
    net = PhysicalNetwork(name=network_name)
    if network_topology == "Reduced":
        network_nodes_file = "input/ReducedTopo/01-NetworkNodes.csv"
        network_connections_file = "input/ReducedTopo/02-NetworkConnections.csv"
    elif network_topology == "Regional":
        network_nodes_file = "input/RegionalTopo/01-NetworkNodes.csv"
        network_connections_file = "input/RegionalTopo/02-NetworkConnections.csv"
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
        algo = RamyILP(net, new_requests=new_requests, hosted_requests=hosted_requests, model_name="DemoModel")
    elif algorithm_name == "ArisILP":
        algo = ArisILP(net, new_requests=new_requests, hosted_requests=hosted_requests)
    elif algorithm_name == "BinpackHeur":
        algo = BinpackHeur(net, new_requests=new_requests, hosted_requests=hosted_requests)
    elif algorithm_name == "SpreadHeur":
        algo = SpreadHeur(net, new_requests=new_requests, hosted_requests=hosted_requests)
    return algo


def feasibility_restoration(algorithm_instance, grouping_method, algorithm_name, net, hosted_requests, new_requests,
                            compute_resource_factor, bw_factor, e2e_delay_factor, propg_delay_factor):
    # Repair Infeas
    algo = algorithm_instance
    inf_analyzer = InfeasAnalyzer(algo.model, compute_resource_factor=compute_resource_factor,
                                  bw_factor=bw_factor, e2e_delay_factor=e2e_delay_factor,
                                  propg_delay_factor=propg_delay_factor)
    recommended_constraints = None
    if grouping_method == "Resource_Location":
        recommended_constraints = "[L1, L2, L3, L4, L5]"
    elif grouping_method == "Constraint_Type":
        recommended_constraints = "[C1, C2, C3, C4]"
    # TODO: get recommended_constraints from the agent
    inf_analyzer.repair_infeas(all_constrs_are_modif=False, constraints_grouping_method=grouping_method,
                               recommeded_consts_groups_to_relax=recommended_constraints)
    repair_result = inf_analyzer.result
    repair_result.print_result()

    # Apply repair and resolve
    if repair_result.is_repaired:
        inf_analyzer.apply_infeas_repair(net, hosted_requests, new_requests)
        new_algo = get_algorithm(net, new_requests, hosted_requests, algorithm_name)
        new_algo.solve(display_result=True, print_decision_variables=False)
        # Todo: when number of requests of type 2 exceeds 9:repair_result.is_repaired is true but new_algo.isFeasible is false
        if new_algo.isFeasible:
            algo.apply_result()
            out_parser = OutputParser(net, hosted_requests, new_requests)
            out_parser.parse_request_assignments()

def get_state_vector(net, request):
        state_vector = []
        # Compute nodes information
        for node in net.get_servers():
            state_vector.append(node.available_specs.cpu)
            state_vector.append(node.available_specs.memory)
            state_vector.append(node.available_specs.storage)
        # Links information
        for link in net.get_links():
            state_vector.append(link.link_specs.available_bandwidth)
            state_vector.append(link.link_specs.propagation_delay)
        # Request information
        state_vector.append(request.request_type)
        gateway_name = request.gateway_router.node_name
        state_vector.append(int(re.search('w(.+?)', gateway_name).group(1)))
        return state_vector

def test_dqn_model(trained_model, max_hops_for_connectivity):

    # Input Parameters
    make_random_new_requests = False
    algorithm_names= ["BinpackHeur", "SpreadHeur", "DoNothing"]    # "RamyILP" is not included
    # algorithm_name = [2]  # RamyILP, BinpackHeur, SpreadHeur, ArisILP
    network_topology = "Reduced"  # "Reduced" or "Regional"

    # Create the network
    net, input_parser = create_network("Net1", network_topology, max_hops_for_connectivity)
    hosted_requests, new_requests = create_requests(input_parser, make_random_new_requests)
    # Apply the placement of the hosted requests (if any)
    input_parser.assign_hosted_requests()

    number_of_success = 0
    number_of_requests = len(new_requests)
    for req in new_requests:
        state = get_state_vector(net, req)
        state = state / np.linalg.norm(state)
        state = np.array(state)
        state = torch.tensor(state, dtype=torch.float)
        prediction = trained_model(state)
        action_index = torch.argmax(prediction).item()
        if action_index == 2:   #Do Nothing Action
            continue
        algorithm_name = algorithm_names[action_index]


        # VNF Placement
        algo = get_algorithm(net, [req], hosted_requests, algorithm_name)

        # Solve the formulated problem
        algo.solve(display_result=False, print_decision_variables=True)

        if isinstance(algo, Heuristic):
            heuristic_result = algo.heuristic_result
            if heuristic_result.is_success:
                # algo.display_result()
                number_of_success += 1
            else:
                print("Heuristic failed")

        elif isinstance(algo, Algorithm):
            # Check Feasibility
            if algo.isFeasible:
                algo.apply_result()
                number_of_success += 1
            else:
                print("Model is Infeasible: Algorithm failed")


        print("Done")
    acceptance_ratio = number_of_success / number_of_requests
    print(f"Acceptance Ratio is {acceptance_ratio * 100}%")


if __name__ == '__main__':
    main()
