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
from CloudDefrag.Visualization.Visualizer import NetworkVisualizer


def main():
    # Create network
    net = PhysicalNetwork(name="Net1")
    input_parser = InputParser(net)
    net_visual = NetworkVisualizer(net)
    net_visual.plot()

    hosted_requests = input_parser.get_all_hosted_requests()
    new_requests = input_parser.get_all_new_requests()
    input_parser.assign_hosted_requests()



    algo = RamyILP(net, new_requests, hosted_requests)
    algo.solve(display_result=True)
    algo.apply_result()


if __name__ == '__main__':
    main()
