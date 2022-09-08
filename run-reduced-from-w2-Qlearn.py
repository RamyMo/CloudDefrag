#!/usr/bin/python3
# The main code of the Simulator
import networkx

from CloudDefrag.Model.Algorithm.BinPack import BinPack
from CloudDefrag.Model.Algorithm.HouILP import HouILP
from CloudDefrag.Model.Algorithm.RamyILP import RamyILP
from CloudDefrag.Model.Algorithm.Request import VMRequest, NewVMRequest, HostedVMRequest
from CloudDefrag.Model.Algorithm.Spread import Spread
from CloudDefrag.Model.Graph.Link import VirtualLink, LinkSpecs, PhysicalLink
from CloudDefrag.Model.Graph.Network import PhysicalNetwork, VirtualNetwork
from CloudDefrag.Model.Graph.Node import Server, VirtualMachine, Router, DummyVirtualMachine
from CloudDefrag.Model.Graph.Specs import Specs
import matplotlib.pyplot as plt
import networkx as nx

from CloudDefrag.Parsing.InputParser import InputParser
from CloudDefrag.Parsing.OutputParser import OutputParser
from CloudDefrag.QLearning.Qlearning import Qlearning
from CloudDefrag.QLearning.VNF_Env import VNF_Env
import time

from CloudDefrag.Visualization.Visualizer import NetworkVisualizer, RequestVisualizer


def main():
    number_of_requests = 2

    start_init_time = time.time()
    env = VNF_Env()
    qlearn = Qlearning(env)
    end_init_time = time.time()
    init_time = end_init_time - start_init_time
    start_learn_time = time.time()
    qlearn.learn()
    end_learn_time = time.time()

    learning_time = end_learn_time - start_learn_time

    start_plot_time = time.time()
    qlearn.plot()
    end_plot_time = time.time()
    plotting_time = end_plot_time - start_plot_time

    # qlearn.generate_qtables_charts()
    # qlearn.generate_qtables_video()

    print("\n ******* Time Summary *******")
    print(f"Initialization Time: {init_time} seconds")
    print(f"Learning Time: {learning_time} seconds")
    print(f"Plotting Time: {plotting_time} seconds")
    print(f"Total Time: {init_time + learning_time + plotting_time} seconds")










    print("\n ******* Done *******")


if __name__ == '__main__':
    main()
