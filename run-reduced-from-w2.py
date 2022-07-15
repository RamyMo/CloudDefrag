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
import matplotlib.pyplot as plt
import networkx as nx

from CloudDefrag.Parsing.InputParser import InputParser
from CloudDefrag.Parsing.OutputParser import OutputParser
from CloudDefrag.Visualization.Visualizer import NetworkVisualizer, RequestVisualizer


def main():
    # Create the network
    net = PhysicalNetwork(name="Net-w2-t1")
    input_parser = InputParser(net, network_nodes_file="input/ReducedNetfromW2Type1/01-NetworkNodes.csv",
                               network_connections_file="input/ReducedNetfromW2Type1/02-NetworkConnections.csv")
    # Draw the network topology
    net_visual = NetworkVisualizer(net)
    net_visual.plot()

    hosted_requests = input_parser.get_all_hosted_requests()
    new_requests = input_parser.get_all_new_requests()
    input_parser.assign_hosted_requests()

    out_parser = OutputParser(net, hosted_requests, new_requests)
    out_parser.parse_net_snapshot(nodes_file_name="output/NetSnapShot/NetworkNodesSnapShot-before.csv",
                                  links_file_name="output/NetSnapShot/NetworkConnectionsSnapShot-before.csv")

    algo = RamyILP(net, new_requests, hosted_requests)
    algo.solve(display_result=True)
    algo.apply_result()

    out_parser.parse_request_assignments()
    out_parser.parse_net_snapshot(nodes_file_name="output/NetSnapShot/NetworkNodesSnapShot-after.csv",
                                  links_file_name="output/NetSnapShot/NetworkConnectionsSnapShot-after.csv")
    print("Done")


if __name__ == '__main__':
    main()
