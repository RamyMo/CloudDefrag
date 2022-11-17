import simpy
import random
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
from CloudDefrag.Visualization.Visualizer import NetworkVisualizer, RequestVisualizer
from CloudDefrag.Model.Algorithm.Request import NewVMRequest


# https://simpy.readthedocs.io/en/latest/

class Simulator:

    def __init__(self, **kwargs) -> None:
        # creates a SimPy Environment
        self._env = simpy.Environment()

        # Initializes a new arrival process connected to the Environment
        self._arrival_rate = 1
        self._departure_rate = 0.5
        self._number_of_requests = kwargs["number_of_requests"] if "number_of_requests" in kwargs else 10
        self._seed = 93
        random.seed(self._seed)

        self._algorithm_name = "RamyILP"  # RamyILP, BinpackHeur, SpreadHeur, ArisILP

        # Initialize Network
        self._network_topology = "Reduced"  # "Reduced" or "Regional"

        # Create the network
        self._net, self._input_parser = create_network("Net1", self._network_topology)

        # Draw the network topology
        self._net_visual = NetworkVisualizer(self._net)
        # net_visual.plot()

        self._result = SimulationResult()
        self.result.number_of_requests = self.number_of_requests


    @property
    def arrival_rate(self):
        return self._arrival_rate

    @arrival_rate.setter
    def arrival_rate(self, value):
        self._arrival_rate = value

    @property
    def departure_rate(self):
        return self._departure_rate

    @departure_rate.setter
    def departure_rate(self, value):
        self._departure_rate = value

    @property
    def number_of_requests(self):
        return self._number_of_requests

    @number_of_requests.setter
    def number_of_requests(self, value):
        self._number_of_requests = value

    @property
    def seed(self):
        return self._seed

    @seed.setter
    def seed(self, value):
        self._seed = value
        random.seed(self._seed)

    @property
    def algorithm_name(self):
        return self._algorithm_name

    @algorithm_name.setter
    def algorithm_name(self, value):
        self._algorithm_name = value

    @property
    def network_topology(self):
        return self._network_topology

    @network_topology.setter
    def network_topology(self, value):
        self._network_topology = value

    @property
    def net(self):
        return self._net

    @property
    def input_parser(self):
        return self._input_parser

    @property
    def net_visual(self):
        return self._net_visual

    @net_visual.setter
    def net_visual(self, value):
        self._net_visual = value

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, value):
        self._result = value

    def arrival_process(self):
        """
            Arrival process, implemented with Simpy in mind
        """
        count = 0
        while count < self.number_of_requests:
            interarrival = random.expovariate(self.arrival_rate)
            yield self._env.timeout(interarrival)
            count += 1
            new_req = self.input_parser.get_random_new_request()
            print(f'Request# {new_req.request_id}, Type: {new_req.request_type}'
                  f' Gateway: {new_req.gateway_router.node_name} arrives at time {self._env.now:5.2f}')

            # Allocate request
            algo = get_algorithm(self.net, [new_req], [], self.algorithm_name)
            # Solve the formulated problem
            algo.solve(display_result=False, print_decision_variables=False)
            is_allocated = False
            if isinstance(algo, Heuristic):
                heuristic_result = algo.heuristic_result
                if heuristic_result.is_success:
                    algo.display_result()
                    is_allocated = True
            elif isinstance(algo, Algorithm):
                # Check Feasibility
                if algo.isFeasible:
                    algo.apply_result()
                    is_allocated = True
            # self.net_visual.interactive_visual()

            # Add the corresponding departure event if allocated
            if is_allocated:
                self._env.process(self.departure_process(new_req))
                self.result.num_of_accept += 1
            else:
                print(f'Blocked Request# {new_req.request_id}, Type: {new_req.request_type}'
                      f' Gateway: {new_req.gateway_router.node_name} arrives at time {self._env.now:5.2f}')
                self.result.num_of_blocks += 1

    def departure_process(self, new_req):
        """
                Departure process, implemented with Simpy in mind
        """
        departure_time = random.expovariate(self.departure_rate)
        yield self._env.timeout(departure_time)
        print(f'Request# {new_req.request_id}, Type: {new_req.request_type}'
              f' Gateway: {new_req.gateway_router.node_name} departs at time {self._env.now:5.2f}')
        new_req.deallocate()

    def start(self):
        self._env.process(self.arrival_process())
        self._env.run()

class SimulationResult:

    def __init__(self) -> None:
        self.number_of_requests = 0
        self.num_of_blocks = 0
        self.num_of_accept = 0

    def print_simulation_result(self):
        print("\n *** Simulation End ***")
        print(f"Total Number of requests = {self.number_of_requests}")
        print(f"Number of Blocks = {self.num_of_blocks}")
        print(f"Number of Accepts = {self.num_of_accept}")
        print(f"Acceptance Percentage = {(self.num_of_accept/self.number_of_requests)*100}%")


def create_network(network_name, network_topology):
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

