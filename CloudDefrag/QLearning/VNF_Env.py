import random
import numpy as np

from CloudDefrag.Model.Algorithm.BinPack import BinPack
from CloudDefrag.Model.Algorithm.Spread import Spread
from CloudDefrag.Model.Graph.Network import PhysicalNetwork
from CloudDefrag.Parsing.InputParser import InputParser
from CloudDefrag.Parsing.OutputParser import OutputParser
from CloudDefrag.Visualization.Visualizer import NetworkVisualizer


class VNF_Env:

    def __init__(self, **kwargs) -> None:
        self.number_of_requests = kwargs["number_of_requests"] if "number_of_requests" in kwargs else 2
        self.requests_allocated_so_far = 0
        self.request_index = 0

        # Create the network
        self._net = PhysicalNetwork(name="Net-w2-t1")
        self._input_parser = InputParser(self._net,
                                         network_nodes_file="input/ReducedNetfromW2Type1/01-NetworkNodes.csv",
                                         network_connections_file="input/ReducedNetfromW2Type1/02-NetworkConnections.csv")

        # # Draw the network topology
        # self._net_visual = NetworkVisualizer(self._net)
        # self._net_visual.plot()

        # Requests
        self._hosted_requests = self._input_parser.get_all_hosted_requests()
        self._new_requests = self._input_parser.get_all_new_requests()
        self._input_parser.assign_hosted_requests()

        # out_parser = OutputParser(self._net, self._hosted_requests, self._new_requests)
        # out_parser.parse_net_snapshot(nodes_file_name=f"output/NetSnapShot/Nodes-before.csv",
        #                               links_file_name=f"output/NetSnapShot/Connection-before.csv")

        self.current_time_step = 0
        self.current_episode = 0

        # States
        # self._number_of_workload_index_values = 3
        self._number_of_compute_index_values = 100
        self._number_of_communication_index_values = 100
        # self._number_of_terminal_index_values = 2
        self.number_of_requests_values = self.number_of_requests

        # Actions
        self._action_space_size = 3

        # Rewards
        self._allocate_all_reward = 100
        self._single_allocate_reward = 10

        # Penalties
        self._blocked_penalty = 10
        self._reallocate_penalty = 2
        self._do_nothing_penalty = 10

        # Reward extremes
        self._lowest_possible_reward = -100
        self._highest_possible_reward = 100

        # Q-table
        # Keeping size simple for now
        # self._q_table_size = (self._number_of_compute_index_values, self._number_of_communication_index_values,
        #                       self._action_space_size)
        self._q_table_size = (self._number_of_compute_index_values, self._number_of_communication_index_values,
                              self.number_of_requests_values, self._action_space_size)
        # self._q_table_size = (self._number_of_compute_index_values, self._number_of_communication_index_values,
        #                       self._number_of_workload_index_values, self._number_of_terminal_index_values,
        #                       self._action_space_size)

        self._current_state = 0

    @property
    def is_done(self):
        if self.requests_allocated_so_far == self.number_of_requests:
            return True
        else:
            return False

    @property
    def allocate_all_reward(self):
        return self._allocate_all_reward

    @property
    def lowest_possible_reward(self) -> int:
        return self._lowest_possible_reward

    @property
    def highest_possible_reward(self):
        return self._highest_possible_reward

    @property
    def q_table_size(self):
        return self._q_table_size

    @property
    def current_state(self):
        return self._current_state

    @current_state.setter
    def current_state(self, value):
        self._current_state = value

    def reset(self):
        # Return initial state
        self._net = PhysicalNetwork(name="Net-w2-t1")
        self._input_parser = InputParser(self._net,
                                         network_nodes_file="input/ReducedNetfromW2Type1/01-NetworkNodes.csv",
                                         network_connections_file="input/ReducedNetfromW2Type1/02-NetworkConnections.csv")
        # Requests
        self._hosted_requests = self._input_parser.get_all_hosted_requests()
        self._new_requests = self._input_parser.get_all_new_requests()
        self._input_parser.assign_hosted_requests()
        self.requests_allocated_so_far = 0
        self.request_index = 0

        initial_state = (self._net.compute_index, self._net.communication_index, self.request_index)
        self.current_state = initial_state
        return initial_state

    def get_random_action(self):
        return np.random.randint(0, self._action_space_size)

    def step(self, action: int):
        new_state = None
        reward = 0  # Initial value for reward

        if action == 0:  # A0: Bin-Pack
            algo = BinPack(self._net, self._new_requests, self._hosted_requests, model_name=f"BinPack")
            algo.solve(display_result=False)
            if algo.isFeasible:
                algo.apply_result()
                reward += self._single_allocate_reward
                self.requests_allocated_so_far += 1
                if self.requests_allocated_so_far == self.number_of_requests:
                    reward += self._allocate_all_reward
            else:
                reward -= self._blocked_penalty
            new_state = (self._net.compute_index, self._net.communication_index, self.request_index)

        elif action == 1:  # A1: Spread
            algo = Spread(self._net, self._new_requests, self._hosted_requests, model_name=f"Spread")
            algo.solve(display_result=False)
            if algo.isFeasible:
                algo.apply_result()
                reward += self._single_allocate_reward
                self.requests_allocated_so_far += 1
                if self.requests_allocated_so_far == self.number_of_requests:
                    reward += self._allocate_all_reward
            else:
                reward -= self._blocked_penalty
            new_state = (self._net.compute_index, self._net.communication_index, self.request_index)

        elif action == 2:  # A2: Do-Nothing
            new_state = self.current_state
            reward -= self._do_nothing_penalty

        if self.requests_allocated_so_far == self.number_of_requests:
            done = True
        else:
            done = False

        self.current_state = new_state
        self.request_index += 1

        return new_state, reward, done
