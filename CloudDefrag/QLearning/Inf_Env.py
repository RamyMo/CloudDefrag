import random
import numpy as np

import gurobipy as gp
from gurobipy import GRB
from gurobipy.gurobipy import Model

from CloudDefrag.InfeasAnalysis.InfeasAnalysis import InfeasAnalyzer
from CloudDefrag.InfeasAnalysis.iis.RepairResult import RepairResult
from CloudDefrag.Model.Algorithm.RamyILP import RamyILP
from CloudDefrag.Model.Graph.Network import PhysicalNetwork
from CloudDefrag.Parsing.InputParser import InputParser
from CloudDefrag.Parsing.OutputParser import OutputParser
from CloudDefrag.Visualization.Visualizer import NetworkVisualizer
from CloudDefrag.InfeasAnalysis.iis import IISCompute
from CloudDefrag.InfeasAnalysis.iis.ModelLib import AdvancedModel
import gc


class Inf_Env:

    def __init__(self, model_path, **kwargs) -> None:
        self._model_path = model_path
        self._original_model = gp.read(model_path)
        self._advanced_original_model = AdvancedModel(self._original_model)
        self._modified_model = gp.read(model_path)
        self.current_time_step = 0
        self.current_episode = 0
        # States
        self._number_of_soft_constraints_groups = 4  # 4 or 8 if we consider all constraints
        self._number_of_soft_constraints_groups_values = 2 ** self._number_of_soft_constraints_groups

        # Actions
        self._action_space_size = 5  # 5 Actions (for 4 constraints) + 1 do nothing action

        # Rewards
        self._fixed_infeas_reward = 100
        self._do_nothing_reward = 0

        # Penalties
        self._action_penalty = 10
        self._select_all_constrs_penalty = self._action_penalty
        self._pick_previous_constraint_penalty = 2 * self._action_penalty
        self._pick_constraint_after_fixing_infeas_penalty = self._action_penalty
        self._do_nothing_penalty = self._action_penalty
        self._hard_constraint_penalty = 0

        # Reward extremes
        self._lowest_possible_reward = -5
        self._highest_possible_reward = 5

        # Q-table
        # Keeping size simple for now
        self._q_table_size = (2, 2, 2, 2, self._action_space_size)

        self._current_state = (0, 0, 0, 0)

    @property
    def action_space_size(self):
        return self._action_space_size

    @property
    def original_model(self):
        return self._original_model

    @property
    def advanced_original_model(self):
        return self._advanced_original_model

    @property
    def modified_model(self):
        return self._modified_model

    @modified_model.setter
    def modified_model(self, model):
        self._modified_model = model

    @property
    def advanced_modified_model(self):
        return AdvancedModel(self.modified_model)

    @property
    def model_path(self):
        return self._model_path

    @property
    def is_modified_model_feasible(self):
        return IISCompute.isFeasible(self.modified_model)

    @property
    def is_original_model_feasible(self):
        return IISCompute.isFeasible(self.original_model)

    @property
    def is_done(self):
        if self.is_modified_model_feasible:
            return True
        else:
            return False

    @property
    def fixed_infeasibility_reward(self):
        return self._fixed_infeas_reward

    @property
    def do_nothing_reward(self):
        return self._do_nothing_reward

    @property
    def do_nothing_penalty(self):
        return self._do_nothing_penalty

    @property
    def action_penalty(self):
        return self._action_penalty

    @property
    def hard_constraint_penalty(self):
        return self._hard_constraint_penalty

    @property
    def select_all_constrs_penalty(self):
        return self._select_all_constrs_penalty

    @property
    def pick_previous_constraint_penalty(self):
        return self._pick_previous_constraint_penalty

    @property
    def pick_constraint_after_fixing_infeas_penalty(self):
        return self._pick_constraint_after_fixing_infeas_penalty

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

    @property
    def number_of_soft_constraints_groups(self):
        return self._number_of_soft_constraints_groups

    def reset(self):
        # Return initial state
        initial_state = (0, 0, 0, 0)
        self.current_state = initial_state
        self.modified_model = gp.read(self.model_path)
        return initial_state

    def get_random_action(self):
        return np.random.randint(0, self._action_space_size)

    def take_action(self, action: int):
        new_state = None
        current_state_as_list = list(self.current_state)
        new_state_as_list = current_state_as_list.copy()
        reward = 0  # Initial value for reward
        done = False

        if IISCompute.isFeasible(self.modified_model):  # System is already feasible
            done = True
            if action == self._action_space_size - 1:  # Do nothing action
                reward += self.do_nothing_reward
                new_state = self.current_state
            else:
                reward -= self.pick_constraint_after_fixing_infeas_penalty
                # if 3 < action < self._action_space_size - 1:                # Hard constraint action
                #     reward -= self.hard_constraint_penalty
                if current_state_as_list[action] == 1:  # Same constraint was relaxed before
                    reward -= self.pick_previous_constraint_penalty
                    new_state = tuple(current_state_as_list)  # Stays in the same state
                else:  # Constraint was not relaxed before
                    new_state_as_list[action] = 1
                    new_state = tuple(new_state_as_list)
        else:  # System is infeasible
            if action == self._action_space_size - 1:  # Do nothing penalty
                new_state = self.current_state
                reward -= self.do_nothing_penalty  # Penalized for not taking an action
            # elif 3 < action < self._action_space_size - 1:                # Hard constraint action
            #     reward -= self.hard_constraint_penalty
            #     if current_state_as_list[action] == 1:                      # Same constraint was relaxed before
            #         reward -= self.pick_previous_constraint_penalty
            #         new_state = tuple(current_state_as_list)                # Stays in the same state
            #     else:                                                       # Constraint was not relaxed before
            #         new_state_as_list[action] = 1
            #         new_state = tuple(new_state_as_list)
            #         reward -= self.action_penalty
            else:  # Soft constraint Action
                if current_state_as_list[action] == 1:  # Same constraint was relaxed before
                    reward -= self.pick_previous_constraint_penalty
                    new_state = tuple(current_state_as_list)  # Stays in the same state
                else:  # Constraint was not relaxed before
                    new_state_as_list[action] = 1
                    new_state = tuple(new_state_as_list)
                    # Relax the corresponding constraint group
                    self.modified_model = self.advanced_modified_model.dropModifiableConstraintsGroup(
                        f"C{(action + 1)}")

                    if IISCompute.isFeasible(self.modified_model):
                        reward += self.fixed_infeasibility_reward
                        done = True
                    else:
                        reward -= self.action_penalty

        if new_state == (1, 1, 1, 1):
            reward -= self.select_all_constrs_penalty

        return new_state, reward, done

    def step(self, action: int):
        new_state, reward, done = self.take_action(action)
        self.current_state = new_state
        return new_state, reward, done

    def evaluate(self, final_state):
        path = self.model_path
        model = gp.read(path)
        constrs = ""
        if final_state[0] == 1:
            constrs += " C1"
        if final_state[1] == 1:
            constrs += " C2"
        if final_state[2] == 1:
            constrs += " C3"
        if final_state[3] == 1:
            constrs += " C4"

        inf_analyzer = InfeasAnalyzer(model)
        inf_analyzer.repair_infeas(all_constrs_are_modif=False, recommeded_consts_groups_to_relax=constrs)
        repair_result = inf_analyzer.result
        cost, time = repair_result.repair_cost, repair_result.repair_exec_time
        return cost, time


class Inf_Env_Location:

    def __init__(self, network_nodes_file, network_connections_file, agent_gateway, **kwargs) -> None:

        # Create the network for training
        self._net = PhysicalNetwork(name="Net1_Training")
        self._network_nodes_file = network_nodes_file
        self._network_connections_file = network_connections_file
        self._agent_gateway = agent_gateway
        self._input_parser = InputParser(self._net, network_nodes_file=self._network_nodes_file,
                                         network_connections_file=self._network_connections_file)
        # Get the requests for initial state
        self._hosted_requests_initial = self._input_parser.get_all_hosted_requests()
        # new_requests = input_parser.get_all_new_requests()
        self._new_requests_initial, self._req_dist_initial = self._input_parser.get_random_new_requests_from_gateway \
            (self.agent_gateway, seed_number=0)  # This bypass requests dist. file
        self._new_requests_current, self._req_dist_current = self._new_requests_initial, self._req_dist_initial

        self._current_algo = None
        self._current_model = None      # self._current_model and self._modified_model are same
        self._modified_model = None

        # Initialize Time
        self.current_time_step = 0
        self.current_episode = 0

        # States
        self._number_of_soft_constraints_groups = 5  # 5 Locations
        self._number_of_soft_constraints_groups_values = 2 ** self._number_of_soft_constraints_groups

        # Actions
        self._action_space_size = 6  # 6 Actions (for 5 locations) + 1 do nothing action
        self.location_constrs_dict = {0: ["w3", "s3", "s4"], 1: ["w2", "s8"], 2: ["s1", "s2", "s5", "s6", "s7", "w1"],
                                      3: ["w6"], 4: ["s9", "s10", "s11", "w7", "w8", "w4", "w5"], 5: []}

        # Rewards
        self._fixed_infeas_reward = 100
        self._do_nothing_reward = 0

        # Penalties
        self._action_penalty = 10
        self._select_all_constrs_penalty = self._action_penalty
        self._pick_previous_constraint_penalty = 2 * self._action_penalty
        self._pick_constraint_after_fixing_infeas_penalty = self._action_penalty
        self._do_nothing_penalty = self._action_penalty
        self._hard_constraint_penalty = 0

        # Reward extremes
        self._lowest_possible_reward = -5
        self._highest_possible_reward = 5

        # Q-table
        # Keeping size simple for now
        self._q_table_size = (2, 2, 2, 2, 2, 10, self._action_space_size)

        # self._initial_state = (0, 0, 0, 0, 0, self._req_dist_initial[0],
        #                        self._req_dist_initial[1], self._req_dist_initial[2])  # (L1, L2, L3, L4, L5, T1, T2, T3)

        self._initial_state = (0, 0, 0, 0, 0, self._req_dist_initial[0],
                               )  # (L1, L2, L3, L4, L5, T1)

        self._current_state = self._initial_state

    @property
    def agent_gateway(self):
        return self._agent_gateway

    @agent_gateway.setter
    def agent_gateway(self, value):
        self._agent_gateway = value

    @property
    def initial_state(self):
        return self._initial_state

    @property
    def action_space_size(self):
        return self._action_space_size

    @property
    def modified_model(self):
        return self._modified_model

    @modified_model.setter
    def modified_model(self, model):
        self._modified_model = model

    @property
    def is_modified_model_feasible(self):
        return IISCompute.isFeasible(self.modified_model)

    @property
    def is_done(self):
        if self.is_modified_model_feasible:
            return True
        else:
            return False

    @property
    def fixed_infeasibility_reward(self):
        return self._fixed_infeas_reward

    @property
    def do_nothing_reward(self):
        return self._do_nothing_reward

    @property
    def do_nothing_penalty(self):
        return self._do_nothing_penalty

    @property
    def action_penalty(self):
        return self._action_penalty

    @property
    def hard_constraint_penalty(self):
        return self._hard_constraint_penalty

    @property
    def select_all_constrs_penalty(self):
        return self._select_all_constrs_penalty

    @property
    def pick_previous_constraint_penalty(self):
        return self._pick_previous_constraint_penalty

    @property
    def pick_constraint_after_fixing_infeas_penalty(self):
        return self._pick_constraint_after_fixing_infeas_penalty

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

    @property
    def number_of_soft_constraints_groups(self):
        return self._number_of_soft_constraints_groups

    def reset(self):
        # Return initial state
        # Todo: optimize memory usage for self._new_requests_current, self._current_algo, self._current_model
        self._new_requests_current, self._req_dist_current = self._input_parser.get_random_new_requests_from_gateway \
            (self.agent_gateway)  # This bypass requests dist. file

        # Dispose old current_algo model
        if self._current_algo:
            self._current_algo.model.dispose()
            self._current_algo.model = None
            self._current_algo = None

        self._current_algo = RamyILP(self._net, self._new_requests_current, self._hosted_requests_initial)
        self._current_model = self._current_algo.model

        # initial_state = (0, 0, 0, 0, 0, self._req_dist_initial[0],
        #                  self._req_dist_initial[1], self._req_dist_initial[2])  # (L1, L2, L3, L4, L5, T1, T2, T3)

        initial_state = (0, 0, 0, 0, 0, self._req_dist_initial[0])  # (L1, L2, L3, L4, L5, T1)

        self.current_state = initial_state
        self.modified_model = self._current_algo.model              # Note this statement
        return initial_state

    def get_random_action(self):
        return np.random.randint(0, self._action_space_size)

    def take_action(self, action: int):
        new_state = None
        current_state_as_list = list(self.current_state)
        new_state_as_list = current_state_as_list.copy()
        reward = 0  # Initial value for reward
        done = False

        if IISCompute.isFeasible(self.modified_model):  # System is already feasible
            done = True
            if action == self._action_space_size - 1:  # Do nothing action
                reward += self.do_nothing_reward
                new_state = self.current_state
            else:
                reward -= self.pick_constraint_after_fixing_infeas_penalty
                # if 3 < action < self._action_space_size - 1:                # Hard constraint action
                #     reward -= self.hard_constraint_penalty
                if current_state_as_list[action] == 1:  # Same constraint was relaxed before
                    reward -= self.pick_previous_constraint_penalty
                    new_state = tuple(current_state_as_list)  # Stays in the same state
                else:  # Constraint was not relaxed before
                    new_state_as_list[action] = 1
                    new_state = tuple(new_state_as_list)
        else:  # System is infeasible
            if action == self._action_space_size - 1:  # Do nothing penalty
                new_state = self.current_state
                reward -= self.do_nothing_penalty  # Penalized for not taking an action
            else:  # Soft constraint Action
                if current_state_as_list[action] == 1:  # Same constraint was relaxed before
                    reward -= self.pick_previous_constraint_penalty
                    new_state = tuple(current_state_as_list)  # Stays in the same state
                else:  # Constraint was not relaxed before
                    new_state_as_list[action] = 1
                    new_state = tuple(new_state_as_list)

                    # Relax the corresponding constraint group
                    constraints_group = self.location_constrs_dict[action]
                    for c in self.modified_model.getConstrs():
                        if any(x in c.ConstrName for x in constraints_group):
                            self.modified_model.remove(c)
                    self.modified_model.update()

                    if IISCompute.isFeasible(self.modified_model):
                        reward += self.fixed_infeasibility_reward
                        done = True
                    else:
                        reward -= self.action_penalty

        if all(i == 1 for i in list(new_state)[0:self._action_space_size - 1]):
            reward -= self.select_all_constrs_penalty

        return new_state, reward, done

    def step(self, action: int):
        new_state, reward, done = self.take_action(action)
        self.current_state = new_state
        return new_state, reward, done

    def evaluate(self, final_state):
        model = self.modified_model
        constrs = ""
        if final_state[0] == 1:
            constrs += " L1"
        if final_state[1] == 1:
            constrs += " L2"
        if final_state[2] == 1:
            constrs += " L3"
        if final_state[3] == 1:
            constrs += " L4"
        if final_state[4] == 1:
            constrs += " L4"

        inf_analyzer = InfeasAnalyzer(model)
        inf_analyzer.repair_infeas(all_constrs_are_modif=False, recommeded_consts_groups_to_relax=constrs)
        repair_result = inf_analyzer.result
        cost, time = repair_result.repair_cost, repair_result.repair_exec_time
        return cost, time

    def garbage_collector(self):
        self._current_model.dispose()
        self._current_model = None
        self._current_algo = None
        # gp.disposeDefaultEnv()
        for req in self._new_requests_current:
            req.new_vms_assign_vars = None
            req.new_vlinks_assign_vars = None
            req.requested_vlink_revenue_dict = None
            req.requested_vlink_prop_delay_dict = None
            req.requested_vlink_cost_dict = None
            req.requested_vlink_assign_dict = None
            req.requested_vlinks_prop_delay = None
            req.requested_vlinks_revenue = None
            req.requested_vlinks_combinations = None
            req.requested_vms_combinations = None
            req.requested_vlinks_cost = None
            req.requested_vms_servers_assign_dict = None
            req.requested_vms_servers_cost_dict = None
            req.requested_vms_servers_revenue_dict = None
            req = None

