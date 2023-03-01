import re
import networkx
import numpy as np
import torch
from CloudDefrag.DQN.Agent import Agent
from CloudDefrag.DQN.Agent import train
from CloudDefrag.DQN.Env import Env

from CloudDefrag.DQN_BS3.Agent import Agent as Agent_BS3
from CloudDefrag.DQN_BS3.Agent import train as train_BS3
from CloudDefrag.DQN_BS3.Env import VNFEnv

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
from CloudDefrag.Parsing.InputParser import InputParser
from CloudDefrag.Parsing.OutputParser import OutputParser
from CloudDefrag.Simulator.Simulator import Simulator
from CloudDefrag.Visualization.Visualizer import NetworkVisualizer, RequestVisualizer

def create_network(network_name, network_topology, max_hops_for_connectivity):
    """
    Create a physical network with the given name, topology, and maximum number of hops for connectivity.

    Args:
        network_name (str): The name of the network.
        network_topology (str): The topology of the network, which can be "Reduced" or "Regional".
        max_hops_for_connectivity (int): The maximum number of hops allowed for connectivity between nodes in the network.

    Returns:
        tuple: A tuple of two objects, where the first object is the physical network object and the second object is the input parser object.

    Raises:
        ValueError: If an invalid network topology is provided.

    Example:
        >>> net, input_parser = create_network("MyNetwork", "Reduced", 3)
        >>> net
        PhysicalNetwork(name='MyNetwork')
        >>> input_parser
        <InputParser object at 0x7f2a17a3c790>
    """
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
    """
    Create a set of hosted requests and new requests based on the input parser and a flag indicating whether to generate random new requests.

    Args:
        input_parser (InputParser): An instance of the InputParser class.
        make_random_new_requests (bool, optional): A flag indicating whether to generate random new requests. Defaults to False.

    Returns:
        tuple: A tuple of two lists, where the first list contains the hosted requests and the second list contains the new requests.

    Example:
        >>> input_parser = InputParser(physical_network)
        >>> hosted_requests, new_requests = create_requests(input_parser)
        >>> len(hosted_requests)
        10
        >>> len(new_requests)
        5
    """
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
    Return an instance of an algorithm of the specified type.

    Args:
        net (PhysicalNetwork): The physical network to be used by the algorithm.
        new_requests (List[Request]): The new requests to be assigned by the algorithm.
        hosted_requests (List[Request]): The currently hosted requests in the network.
        algorithm_name (str): The name of the algorithm to be used. Supported algorithm names: "RamyILP", "ArisILP", "BinpackHeur", "SpreadHeur".

    Returns:
        Union[RamyILP, ArisILP, BinpackHeur, SpreadHeur, None]: An instance of the selected algorithm, or None if an invalid algorithm name is provided.

    Example:
        >>> net = PhysicalNetwork(name='MyNetwork')
        >>> new_requests = [Request(id=1, size=10), Request(id=2, size=20)]
        >>> hosted_requests = [Request(id=3, size=15)]
        >>> algorithm_name = "BinpackHeur"
        >>> algorithm = get_algorithm(net, new_requests, hosted_requests, algorithm_name)
        >>> algorithm
        BinpackHeur(net=PhysicalNetwork(name='MyNetwork'), new_requests=[Request(id=1, size=10), Request(id=2, size=20)], hosted_requests=[Request(id=3, size=15)])
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
    """
    Repair any infeasibilities found by the given algorithm instance and apply the repair to the network.

    Args:
        algorithm_instance (RamyILP or ArisILP or BinpackHeur or SpreadHeur): An instance of an algorithm to be used.
        grouping_method (str): The method used to group constraints. Supported values: "Resource_Location", "Constraint_Type".
        algorithm_name (str): The name of the algorithm being used. Supported values: "RamyILP", "ArisILP", "BinpackHeur", "SpreadHeur".
        net (PhysicalNetwork): The physical network to be used.
        hosted_requests (List[Request]): The currently hosted requests in the network.
        new_requests (List[Request]): The new requests to be assigned.
        compute_resource_factor (float): The weight given to the compute resource constraint in the infeasibility analysis.
        bw_factor (float): The weight given to the bandwidth constraint in the infeasibility analysis.
        e2e_delay_factor (float): The weight given to the end-to-end delay constraint in the infeasibility analysis.
        propg_delay_factor (float): The weight given to the propagation delay constraint in the infeasibility analysis.

    Returns:
        None

    Example:
        >>> algorithm_instance = RamyILP(net, new_requests, hosted_requests)
        >>> grouping_method = "Constraint_Type"
        >>> algorithm_name = "RamyILP"
        >>> feasibility_restoration(algorithm_instance, grouping_method, algorithm_name, net, hosted_requests, new_requests, 1.0, 1.0, 1.0, 1.0)
    """
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
    """
    Compute the state vector for the given network and request.

    Args:
        net (PhysicalNetwork): The physical network to be used.
        request (Request): The request for which the state vector is computed.

    Returns:
        List[Union[int, float]]: A list of integers and floats representing the state vector.

    Example:
        >>> net = PhysicalNetwork(name='MyNetwork')
        >>> request = Request(id=1, size=10)
        >>> get_state_vector(net, request)
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 3]
    """
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
    """
    Test the given DQN model on a network with new requests.

    Args:
        trained_model (Linear_QNet): The trained DQN model to be tested.
        max_hops_for_connectivity (int): The maximum number of hops for connectivity.

    Returns:
        None

    Example:
        >>> model = Linear_QNet(input_size=25, hidden_size=256, output_size=3)
        >>> test_dqn_model(model, max_hops_for_connectivity=2)
        Acceptance Ratio is 50%
        {'BinpackHeur': 0, 'SpreadHeur': 1, 'DoNothing': 0, 'RamyILP': 0}
        [0.014678429463171036, 0.0, 0.0, 0.0, 0.0, 0.010147010147010147, 0.0, 0.0, 0.0, 0.008995502248875562, ...]
    """
    # Input Parameters
    make_random_new_requests = False
    algorithm_names = ["BinpackHeur", "SpreadHeur", "DoNothing", "RamyILP"]  # "RamyILP" is not included
    algorithms_dist_dict = {"BinpackHeur": 0, "SpreadHeur": 0, "DoNothing": 0, "RamyILP": 0}
    network_connectivity = []
    # algorithm_name = [2]  # RamyILP, BinpackHeur, SpreadHeur, ArisILP
    network_topology = "Reduced"  # "Reduced" or "Regional"

    # Create the network
    net, input_parser = create_network("Net1", network_topology, max_hops_for_connectivity)
    hosted_requests, new_requests = create_requests(input_parser, make_random_new_requests)
    # Apply the placement of the hosted requests (if any)
    input_parser.assign_hosted_requests()

    # # Draw the network topology
    net_visual = NetworkVisualizer(net)
    net_visual.interactive_visual()

    number_of_success = 0
    number_of_requests = len(new_requests)
    for req in new_requests:
        # Generate State
        state = get_state_vector(net, req)
        state = state / np.linalg.norm(state)
        state = np.array(state)
        state = torch.tensor(state, dtype=torch.float)
        # Get Action Prediction
        prediction = trained_model(state)
        # Get Action Index
        action_index = torch.argmax(prediction).item()
        if action_index == 2:  # Do Nothing Action
            continue
        # Choose algorithm selected by the action
        algorithm_name = algorithm_names[action_index]
        algorithms_dist_dict[algorithm_name] += 1
        # Apply VNF Placement
        algo = get_algorithm(net, [req], hosted_requests, algorithm_name)

        # Solve the formulated problem
        algo.solve(display_result=False, print_decision_variables=True)
        successful_allocation = False
        # Check if it is heuristic or algorithm
        if isinstance(algo, Heuristic):
            heuristic_result = algo.heuristic_result
            if heuristic_result.is_success:
                # algo.display_result()
                number_of_success += 1
                successful_allocation = True
            else:
                print("Heuristic failed")

        elif isinstance(algo, Algorithm):
            # Check Feasibility
            if algo.isFeasible:
                algo.apply_result()
                number_of_success += 1
                successful_allocation = True
            else:
                print("Model is Infeasible: Algorithm failed")

        if successful_allocation:
            net_visual.interactive_visual()
        print("Done")
        network_connectivity.append(net.compute_gateway_connectivity())

    acceptance_ratio = number_of_success / number_of_requests
    print(f"Acceptance Ratio is {acceptance_ratio * 100}%")
    print(algorithms_dist_dict)
    print(network_connectivity)
    i = 1
    for value in network_connectivity:
        if i % 5 == 0 or i == 1:
            print(f"({i}, {value*100*i})",  end='')
        i += 1


def test_example_feas():
    """
    Test the feasibility of the network allocation using the given algorithm and network topology.

    Args:
        None

    Returns:
        None

    Example:
        >>> test_example_feas()
        Problem is feasible: True
        Objective function value: 94.00000000000001
        Request Assignments:
        Req1:  ['W1->v4->v7', 'W1->v4->v8']
        Req2:  ['W1->v3->v6', 'W1->v3->v5']
        Req3:  ['W1->v2->v5', 'W1->v2->v6']
        Req4:  ['W1->v1->v5', 'W1->v1->v6']
    """
    algorithm_name = "RamyILP"  # RamyILP, BinpackHeur, SpreadHeur, ArisILP
    network_topology = "Reduced"  # "Reduced" or "Regional"
    # Create the network
    net, input_parser = create_network("Net1", network_topology, 1)

    # Draw the network topology
    net_visual = NetworkVisualizer(net)
    net_visual.plot()

    hosted_requests, new_requests = create_requests(input_parser, False)
    algo = get_algorithm(net, new_requests, hosted_requests, algorithm_name)
    algo.solve(display_result=True, print_decision_variables=True)


def test_with_one_method(algorithm_name):
    """
    Test the network allocation using the given algorithm and network topology.

    Args:
        algorithm_name (str): The name of the algorithm to use. Supported algorithms: RamyILP, ArisILP, BinpackHeur, SpreadHeur

    Returns:
        None

    Example:
        >>> test_with_one_method("SpreadHeur")
        Acceptance Ratio is 100.0%
    """
    # Input Parameters
    make_random_new_requests = False
    # algorithm_name = "SpreadHeur"  # RamyILP, BinpackHeur, SpreadHeur, ArisILP
    network_topology = "Reduced"  # "Reduced" or "Regional"

    # Request parameters
    single_request_allocation = True

    # Feasibility Restoration Parameters
    enable_infeas_repair = False
    grouping_method = "Resource_Location"  # "Resource_Location" or "Resource_Location"
    compute_resource_factor = 500
    bw_factor = 40
    e2e_delay_factor = 5
    propg_delay_factor = 10

    # Create the network
    net, input_parser = create_network("Net1", network_topology, 1)

    # Draw the network topology
    net_visual = NetworkVisualizer(net)
    net_visual.plot()
    hosted_requests, new_requests = create_requests(input_parser, make_random_new_requests)

    number_of_success = 0
    number_of_requests = len(new_requests)
    for req in new_requests:
        algo = get_algorithm(net, [req], hosted_requests, algorithm_name)
        # Solve the formulated problem
        algo.solve(display_result=False, print_decision_variables=True)
        successful_allocation = False
        # Check if it is heuristic or algorithm
        if isinstance(algo, Heuristic):
            heuristic_result = algo.heuristic_result
            if heuristic_result.is_success:
                # algo.display_result()
                number_of_success += 1
                successful_allocation = True
            else:
                print("Heuristic failed")

        elif isinstance(algo, Algorithm):
            # Check Feasibility
            if algo.isFeasible:
                algo.apply_result()
                number_of_success += 1
                successful_allocation = True
            else:
                print("Model is Infeasible: Algorithm failed")

        if successful_allocation:
            net_visual.interactive_visual()
        print("Done")

    acceptance_ratio = number_of_success / number_of_requests
    print(f"Acceptance Ratio is {acceptance_ratio * 100}%")