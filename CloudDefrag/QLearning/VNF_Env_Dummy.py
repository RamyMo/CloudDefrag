import random
import numpy as np


class VNF_Env:

    def __init__(self, **kwargs) -> None:
        # States
        self._number_of_workload_index_values = 3
        self._number_of_compute_index_values = 10
        self._number_of_communication_index_values = 10
        self._number_of_terminal_index_values = 2

        # Actions
        self._action_space_size = 4

        # Rewards
        self._allocate_all_reward = 100
        self._single_allocate_reward = 2

        # Penalties
        self._move_penalty = 1
        self._blocked_penalty = 5
        self._reallocate_penalty = 2

        # Reward extremes
        self._lowest_possible_reward = -5
        self._highest_possible_reward = 2

        # Q-table
        # Keeping size simple for now
        self._q_table_size = (self._number_of_compute_index_values, self._number_of_communication_index_values,
                              self._action_space_size)
        # self._q_table_size = (self._number_of_compute_index_values, self._number_of_communication_index_values,
        #                       self._number_of_workload_index_values, self._number_of_terminal_index_values,
        #                       self._action_space_size)

        self._current_state = 0

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
        # Return a random state
        num_of_state_elements = len(self.q_table_size) - 1  # -1 to exclude action space
        random_state = []
        for i in range(num_of_state_elements):
            random_state.append(random.randint(0, self.q_table_size[i] - 1))
        random_state = tuple(random_state)
        self.current_state = random_state
        return random_state

    def get_random_action(self):
        return np.random.randint(0, self._action_space_size)

    def step(self, action: int):
        new_discrete_state = None
        reward = 0  # Initial value for reward
        if action == 0:  # A1: Bin-Pack
            reward += self._single_allocate_reward
            reward -= self._move_penalty
            new_discrete_state = (random.randint(5, 9), random.randint(0, 2))
            # new_discrete_state = (random.randint(49, 99), random.randint(0, 24))
        elif action == 1:  # A2: Spread
            reward += self._single_allocate_reward
            reward -= self._move_penalty
            new_discrete_state = (random.randint(0, 4), random.randint(0, 4))
        elif action == 2:  # A3: Reallocate
            reward += self._single_allocate_reward
            reward -= self._reallocate_penalty
            reward -= self._move_penalty
            new_discrete_state = (random.randint(0, 4), random.randint(0, 4))
        elif action == 3:  # A4: Do-Nothing
            reward = 0
            new_discrete_state = self.current_state
        done = False
        self.current_state = new_discrete_state
        return new_discrete_state, reward, done
