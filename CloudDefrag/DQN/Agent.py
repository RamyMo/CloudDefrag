import torch
import random
import numpy as np
from collections import deque
from CloudDefrag.DQN.Env import Env
from CloudDefrag.DQN.Model import Linear_QNet, QTrainer
from CloudDefrag.DQN.Helper import plot

MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.001


class Agent:

    def __init__(self, env):
        self.n_games = 0
        self.epsilon = 0  # randomness
        self.num_of_exploration_episodes = 100  # After num_of_exploration_episodes agent will full exploit
        self.gamma = 0.9  # discount rate
        self.env = env
        self.memory = deque(maxlen=MAX_MEMORY)  # popleft()
        self.num_of_neurons_per_layer = 256
        self.model = Linear_QNet(self.env.state_vector_size, self.num_of_neurons_per_layer, self.env.action_space_size)
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)

    def get_state(self):
        state = self.env.current_state
        state = state / np.linalg.norm(state)

        return np.array(state)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))  # popleft if MAX_MEMORY is reached

    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE)  # list of tuples
        else:
            mini_sample = self.memory

        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)
        # for state, action, reward, nexrt_state, done in mini_sample:
        #    self.trainer.train_step(state, action, reward, next_state, done)

    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self, state):
        # random moves: tradeoff exploration / exploitation
        self.epsilon = self.num_of_exploration_episodes - self.n_games  #Explore or Exploit
        final_move = [0] * self.env.action_space_size
        if random.randint(0, self.num_of_exploration_episodes) < self.epsilon:  #Explore
            move = np.random.randint(0, self.env.action_space_size)
            final_move[move] = 1
        else:   #Exploit
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()
            final_move[move] = 1

        return final_move


def train(game, agent):
    plot_scores = []
    plot_mean_scores = []

    plot_rfds = []
    plot_mean_rfds = []
    total_rfd = 0

    total_score = 0
    record = 0

    number_of_steps = 0
    total_game_reward = 0

    while True:
        # get old state
        state_old = agent.get_state()

        # get move
        final_move = agent.get_action(state_old)

        # perform move and get new state
        state_new, reward, done, score = game.step(final_move)

        total_game_reward += reward

        # train short memory
        agent.train_short_memory(state_old, final_move, reward, state_new, done)

        # remember
        agent.remember(state_old, final_move, reward, state_new, done)

        number_of_steps += 1

        if done:
            # train long memory, plot result
            game.reset()
            agent.n_games += 1
            agent.train_long_memory()
            average_game_reward = total_game_reward / number_of_steps
            number_of_steps = 0
            total_game_reward = 0

            if score > record:
                record = score
                agent.model.save()

            print('Game', agent.n_games, 'Score', score, 'Record:', record)

            plot_scores.append(score)
            total_score += score
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)
            plot(plot_scores, plot_mean_scores)

            print('Trial', agent.n_games, 'Score', score, 'Record:', record, 'Average Score', mean_score)

            # if mean_score > game.number_of_requests - 4:
            #     break


            # plot_rfds.append(100 - average_game_reward)
            # total_rfd += 100 - average_game_reward
            # mean_rfd = total_rfd / agent.n_games
            # plot_mean_rfds.append(mean_rfd)
            # plot(plot_rfds, plot_mean_rfds)

if __name__ == '__main__':
    train()