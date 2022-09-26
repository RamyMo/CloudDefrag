#!/usr/bin/python3
# The main code of the Simulator
import networkx

from CloudDefrag.Model.Algorithm.HouILP import HouILP
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

    hosted_requests = input_parser.get_all_hosted_requests()
    new_requests = input_parser.get_all_new_requests()
    input_parser.assign_hosted_requests()



    algo = RamyILP(net, new_requests, hosted_requests)
    algo.solve(display_result=True)

    if algo.isFeasible:
        algo.apply_result()
        out_parser = OutputParser(net, hosted_requests, new_requests)
        out_parser.parse_request_assignments()
    else:
        inf_analyzer = InfeasAnalyzer(algo.model)
        # inf_analyzer.repair_infeas(all_constrs_are_modif=False)
        inf_analyzer.repair_infeas(all_constrs_are_modif=False, recommeded_consts_groups_to_relax="C1, C2")
        repair_result = inf_analyzer.result
        repair_result.print_result()
    print("Done")


if __name__ == '__main__':
    main()
