#!/usr/bin/python3
from CloudDefrag.Misc.misc import *


def doublecheckenv():
    episodes = 10
    max_hops_for_connectivity = 2
    # Test Env
    env = VNFEnv(max_hops_for_connectivity=max_hops_for_connectivity)
    for episode in range(episodes):
        done = False
        obs = env.reset()
        step = 0
        total_reward = 0
        while not done:  # not done:
            random_action = env.action_space.sample()
            obs, reward, done, info = env.step(random_action)
            print(f"Episode: {episode + 1},     Step: {step + 1}     Action: {random_action},    Reward: {reward}")
            total_reward += reward
            step += 1
        print(f"Episode: {episode + 1},     Total Reward: {total_reward},   Score: {info['score']}")

if __name__ == '__main__':
    doublecheckenv()
