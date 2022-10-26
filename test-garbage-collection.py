import gurobipy as gp
from gurobipy import GRB
from gurobipy.gurobipy import Model
from CloudDefrag.InfeasAnalysis.InfeasAnalysis import InfeasAnalyzer
from CloudDefrag.InfeasAnalysis.iis import IISCompute
from CloudDefrag.InfeasAnalysis.iis.ModelLib import AdvancedModel
from CloudDefrag.InfeasAnalysis.iis.RepairResult import RepairResult
from CloudDefrag.Model.Algorithm.ArisILP import ArisILP
from CloudDefrag.Model.Algorithm.BinpackHeur import BinpackHeur
from CloudDefrag.Model.Algorithm.RamyILP import RamyILP
from CloudDefrag.Model.Graph.Network import PhysicalNetwork
from CloudDefrag.Parsing.InputParser import InputParser
from CloudDefrag.QLearning.Inf_Env import Inf_Env, Inf_Env_Location
from CloudDefrag.QLearning.Qlearning import Qlearning
import tracemalloc
import numpy as np
import time


def main():
    tracemalloc.start()
    algos = []
    adv_models = []
    for i in range(20):
        snapshot1 = tracemalloc.take_snapshot()
        algos.append(get_algo_instance())
        adv_models.append(AdvancedModel(algos[i].model))
        snapshot2 = tracemalloc.take_snapshot()
        stats = snapshot2.compare_to(snapshot1, 'lineno')
        print(f"After creating algo No. {i+1}")
        for stat in stats[:10]:
            print(stat)

    for i in range(20):
        snapshot1 = tracemalloc.take_snapshot()
        algos[i].model.dispose()
        algos[i] = None
        adv_models[i].model.dispose()
        adv_models[i] = None
        snapshot2 = tracemalloc.take_snapshot()
        stats = snapshot2.compare_to(snapshot1, 'lineno')
        print(f"After disposing algo No. {i+1}")
        for stat in stats[:10]:
            print(stat)


    for i in range(60):
        snapshot1 = tracemalloc.take_snapshot()
        time.sleep(1)
        snapshot2 = tracemalloc.take_snapshot()
        stats = snapshot2.compare_to(snapshot1, 'lineno')
        print(f"After {i+1} seconds of disposing")
        for stat in stats[:10]:
            print(stat)





def get_algo_instance():
    algorithm_name = "RamyILP"
    # Create the network
    net, input_parser = create_network("Net1")
    # Create the requests
    make_random_new_requests = True
    hosted_requests, new_requests = create_requests(input_parser, make_random_new_requests)

    # Apply the placement of the hosted requests (if any)
    input_parser.assign_hosted_requests()
    algo = get_algorithm(net, new_requests, hosted_requests, algorithm_name)
    # # Solve the formulated problem
    # algo.solve(display_result=True)
    return algo


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
