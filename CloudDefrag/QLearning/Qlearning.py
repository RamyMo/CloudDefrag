import time
# import cv2
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import style
from mpl_toolkits.mplot3d import axes3d
import tracemalloc
from CloudDefrag.QLearning.VNF_Env import VNF_Env


class Qlearning:
    def __init__(self, env, **kwargs) -> None:

        # Environment
        self.env = env

        # Q-Learning settings
        self._learning_rate = kwargs["learning_rate"] if "learning_rate" in kwargs else 0.1
        self._discount_factor = kwargs["discount_factor"] if "discount_factor" in kwargs else 0.95
        self._num_of_episodes = kwargs["num_of_episodes"] if "num_of_episodes" in kwargs else 4000

        # Exploration settings
        self._epsilon = kwargs["epsilon"] if "epsilon" in kwargs else 1  # not a constant, qoing to be decayed
        self._start_epsilon_decaying = kwargs["start_epsilon_decaying"] if "start_epsilon_decaying" in kwargs else 1
        self._end_epsilon_decaying = kwargs["end_epsilon_decaying"] if "end_epsilon_decaying" in kwargs \
            else self._num_of_episodes // 2
        self._epsilon_decay_value = self._epsilon / (self._end_epsilon_decaying - self._start_epsilon_decaying)
        self._number_of_steps_per_episode = 10

        # Results Window Size
        # Results Window size is 1000 Episodes
        self._show_every = kwargs["show_every"] if "show_every" in kwargs else 100

        # Create the Q-table
        self._q_table = np.random.uniform(low=env.lowest_possible_reward, high=env.highest_possible_reward,
                                          size=env.q_table_size)

        # For stats
        self._ep_rewards = []
        self._aggr_ep_rewards = {'ep': [], 'avg': [], 'max': [], 'min': []}

    @property
    def q_table(self):
        return self._q_table

    def learn(self) -> None:
        tracemalloc_enabled = False

        if tracemalloc_enabled:
            tracemalloc.start()         # Start monitoring the memory for leaks


        EPISODES = self._num_of_episodes
        SHOW_EVERY = self._show_every
        env = self.env
        epsilon = self._epsilon
        q_table = self._q_table
        LEARNING_RATE = self._learning_rate
        DISCOUNT = self._discount_factor
        START_EPSILON_DECAYING = self._start_epsilon_decaying
        END_EPSILON_DECAYING = self._end_epsilon_decaying
        epsilon_decay_value = self._epsilon_decay_value
        ep_rewards = self._ep_rewards
        aggr_ep_rewards = self._aggr_ep_rewards

        # Holder of the best current cost and time solution
        current_best_cost = -1
        current_best_time = -1

        if tracemalloc_enabled:
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')
            print("[ Top 10 ] before episodes loop")
            for stat in top_stats[:10]:
                print(stat)



        for episode in range(0, EPISODES + 1):

            if tracemalloc_enabled:
                snapshot1 = tracemalloc.take_snapshot()

            episode_reward = 0
            if episode % SHOW_EVERY == 0:
                print(episode)
                render = True
            else:
                render = False
            discrete_state = env.reset()
            done = False

            # Use the first for VNF placement problem
            # for i in range(env.number_of_requests):               # This is the first
            for i in range(env.number_of_soft_constraints_groups):  # Steps
                if np.random.random() > epsilon:
                    # Get action from Q table
                    action = np.argmax(q_table[discrete_state])
                else:
                    # Get random action
                    action = env.get_random_action()
                new_discrete_state, reward, done = env.step(action)
                episode_reward += reward
                if episode % SHOW_EVERY == 0:
                    pass
                    # env.render()
                    # time.sleep(0.01)

                # If simulation did not end yet after last step - update Q table
                if not done:
                    # Maximum possible Q value in next step (for new state)
                    max_future_q = np.max(q_table[new_discrete_state])
                    # Current Q value (for current state and performed action)
                    current_q = q_table[discrete_state + (action,)]
                    # And here's our equation for a new Q value for current state and action
                    new_q = (1 - LEARNING_RATE) * current_q + LEARNING_RATE * (reward + DISCOUNT * max_future_q)
                    # Update Q table with new Q value
                    q_table[discrete_state + (action,)] = new_q
                    discrete_state = new_discrete_state
                # Simulation ended (for any reason) - if goal position is achived - update Q value with reward directly
                else:   # End of Episode (Terminal State)
                    # print(f"We allocated all requests on episode: {episode}")
                    # q_table[discrete_state + (action,)] = reward
                    # q_table[discrete_state + (action,)] = env.allocate_all_reward  # We get a 100 reward when we allocate all requests
                    # q_table[discrete_state + (action,)] = env.fixed_infeasibility_reward  # We get a 100 reward when we fix infeas

                    # Evaluate the repair at the terminal state and check if it is better than the current best
                    new_cost, new_time = env.evaluate(new_discrete_state)
                    better_cost_reward = 10
                    better_time_reward = 10
                    if current_best_time < 0 and current_best_cost < 0:
                        current_best_time = new_time
                        current_best_cost = new_cost
                    elif new_cost < current_best_cost:
                        reward += better_cost_reward
                        if new_time < current_best_time:
                            reward += better_time_reward
                        current_best_time = new_time
                        current_best_cost = new_cost

                    # Maximum possible Q value in next step (for new state)
                    max_future_q = np.max(q_table[new_discrete_state])
                    # Current Q value (for current state and performed action)
                    current_q = q_table[discrete_state + (action,)]
                    # And here's our equation for a new Q value for current state and action
                    new_q = (1 - LEARNING_RATE) * current_q + LEARNING_RATE * (reward + DISCOUNT * max_future_q)
                    # Update Q table with new Q value
                    q_table[discrete_state + (action,)] = new_q
                    q_table[new_discrete_state + (env.action_space_size - 1,)] = 100



                    break

            # Decaying is being done every episode if episode number is within decaying range
            if END_EPSILON_DECAYING >= episode >= START_EPSILON_DECAYING:
                epsilon -= epsilon_decay_value
            ep_rewards.append(episode_reward)

            if not episode % SHOW_EVERY:
                average_reward = sum(ep_rewards[-SHOW_EVERY:]) / len(ep_rewards[-SHOW_EVERY:])
                aggr_ep_rewards['ep'].append(episode)
                aggr_ep_rewards['avg'].append(average_reward)
                aggr_ep_rewards['max'].append(max(ep_rewards[-SHOW_EVERY:]))
                aggr_ep_rewards['min'].append(min(ep_rewards[-SHOW_EVERY:]))
                print(
                    f'Episode: {episode:>5d}, average reward: {average_reward:>4.1f}, current epsilon: {epsilon:>1.2f}')
                np.save(f"output/Q-tables/{episode}-qtable.npy", q_table)
            # Todo: collect garbage here
            self.env.garbage_collector()

            if tracemalloc_enabled:
                snapshot2 = tracemalloc.take_snapshot()
                stats = snapshot2.compare_to(snapshot1, 'lineno')
                print(f"[ Top 10 ] after episode {episode}")
                for stat in stats[:10]:
                    print(stat)



    def plot(self):
        aggr_ep_rewards = self._aggr_ep_rewards
        plt.plot(aggr_ep_rewards['ep'], aggr_ep_rewards['avg'], label="average rewards")
        plt.plot(aggr_ep_rewards['ep'], aggr_ep_rewards['max'], label="max rewards")
        plt.plot(aggr_ep_rewards['ep'], aggr_ep_rewards['min'], label="min rewards")
        plt.ylabel(f"Reward {self._show_every}ma")
        plt.xlabel("Episode Number")
        plt.legend(loc=5)
        plt.grid(True)
        plt.savefig(f"output/Q-tables/Rewards.png")
        plt.show()

    def generate_qtables_charts(self):

        style.use('ggplot')
        def get_q_color(value, vals, duplicate):
            if value == max(vals) and duplicate[0] == False:
                duplicate[0] = True
                return "green", 1.0
            else:
                return "red", 0.3
        fig = plt.figure(figsize=(12, 9))
        for i in range(0, self._num_of_episodes + self._show_every, self._show_every):

            print(f"Generating Q-Table chart for episode: {i}")
            ax1 = fig.add_subplot(411)
            ax2 = fig.add_subplot(412)
            ax3 = fig.add_subplot(413)
            ax4 = fig.add_subplot(414)

            q_table = np.load(f"output/Q-tables/{i}-qtable.npy")

            for x, x_vals in enumerate(q_table):
                for y, y_vals in enumerate(x_vals):
                    duplicate = [False]
                    ax1.scatter(x, y, c=get_q_color(y_vals[0], y_vals, duplicate)[0], marker="o",
                                alpha=get_q_color(y_vals[0], y_vals, duplicate)[1])
                    ax2.scatter(x, y, c=get_q_color(y_vals[1], y_vals, duplicate)[0], marker="o",
                                alpha=get_q_color(y_vals[1], y_vals, duplicate)[1])
                    ax3.scatter(x, y, c=get_q_color(y_vals[2], y_vals, duplicate)[0], marker="o",
                                alpha=get_q_color(y_vals[2], y_vals, duplicate)[1])
                    ax4.scatter(x, y, c=get_q_color(y_vals[3], y_vals, duplicate)[0], marker="o",
                                alpha=get_q_color(y_vals[3], y_vals, duplicate)[1])

                    ax1.set_title("A1: C1")
                    # ax1.set_ylabel("Communication Index")
                    # ax1.set_xlabel("Comm Index")
                    ax2.set_title("A1: Spread")
                    ax2.set_ylabel("Communication Index")
                    # ax2.set_xlabel("Compute Index")
                    ax3.set_title("A2: Reallocate")
                    # ax3.set_ylabel("Communication Index")
                    # ax3.set_xlabel("Compute Index")
                    ax4.set_title("A3: Do-Nothing")
                    # ax4.set_ylabel("Communication Index")
                    ax4.set_xlabel("Compute Index")

            # plt.show()
            plt.savefig(f"output/Q-tables/Q-tables Charts/{i}.png")
            plt.clf()

    # def generate_qtables_video(self):
    #     # # windows:
    #     # fourcc = cv2.VideoWriter_fourcc(*'XVID')
    #     # Linux:
    #     fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
    #     out = cv2.VideoWriter('output/Q-tables/Q-tables Charts/Qlearn.avi', fourcc, 0.2, (1200, 900))
    #     print("Generating Q-tables video ...")
    #     for i in range(0, self._num_of_episodes + self._show_every, self._show_every):
    #         img_path = f"output/Q-tables/Q-tables Charts/{i}.png"
    #         # print(img_path)
    #         frame = cv2.imread(img_path)
    #         out.write(frame)
    #
    #     out.release()