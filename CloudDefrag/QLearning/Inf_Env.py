import random
import numpy as np

import gurobipy as gp
from gurobipy import GRB
from gurobipy.gurobipy import Model

from CloudDefrag.InfeasAnalysis.InfeasAnalysis import InfeasAnalyzer
from CloudDefrag.InfeasAnalysis.iis.RepairResult import RepairResult
from CloudDefrag.Parsing.OutputParser import OutputParser
from CloudDefrag.Visualization.Visualizer import NetworkVisualizer
from CloudDefrag.InfeasAnalysis.iis import IISCompute
from CloudDefrag.InfeasAnalysis.iis.ModelLib import AdvancedModel


class Inf_Env:

    def __init__(self, model_path, **kwargs) -> None:
        self._model_path = model_path
        self._original_model = gp.read(model_path)
        self._advanced_original_model = AdvancedModel(self._original_model)
        self._modified_model = gp.read(model_path)
        self.current_time_step = 0
        self.current_episode = 0
        # States
        self._number_of_soft_constraints_groups = 4                             # 4 or 8 if we consider all constraints
        self._number_of_soft_constraints_groups_values = 2 ** self._number_of_soft_constraints_groups

        # Actions
        self._action_space_size = 5                     # 5 Actions (for 4 constraints) + 1 do nothing action

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

        if IISCompute.isFeasible(self.modified_model):                  # System is already feasible
            done = True
            if action == self._action_space_size - 1:                   # Do nothing action
                reward += self.do_nothing_reward
                new_state = self.current_state
            else:
                reward -= self.pick_constraint_after_fixing_infeas_penalty
                # if 3 < action < self._action_space_size - 1:                # Hard constraint action
                #     reward -= self.hard_constraint_penalty
                if current_state_as_list[action] == 1:                      # Same constraint was relaxed before
                    reward -= self.pick_previous_constraint_penalty
                    new_state = tuple(current_state_as_list)                # Stays in the same state
                else:                                                       # Constraint was not relaxed before
                    new_state_as_list[action] = 1
                    new_state = tuple(new_state_as_list)
        else:                                                           # System is infeasible
            if action == self._action_space_size - 1:                   # Do nothing penalty
                new_state = self.current_state
                reward -= self.do_nothing_penalty                       # Penalized for not taking an action
            # elif 3 < action < self._action_space_size - 1:                # Hard constraint action
            #     reward -= self.hard_constraint_penalty
            #     if current_state_as_list[action] == 1:                      # Same constraint was relaxed before
            #         reward -= self.pick_previous_constraint_penalty
            #         new_state = tuple(current_state_as_list)                # Stays in the same state
            #     else:                                                       # Constraint was not relaxed before
            #         new_state_as_list[action] = 1
            #         new_state = tuple(new_state_as_list)
            #         reward -= self.action_penalty
            else:                                                           # Soft constraint Action
                if current_state_as_list[action] == 1:                      # Same constraint was relaxed before
                    reward -= self.pick_previous_constraint_penalty
                    new_state = tuple(current_state_as_list)                # Stays in the same state
                else:                                                       # Constraint was not relaxed before
                    new_state_as_list[action] = 1
                    new_state = tuple(new_state_as_list)
                    # Relax the corresponding constraint group
                    self.modified_model = self.advanced_modified_model.dropModifiableConstraintsGroup(f"C{(action + 1)}")

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