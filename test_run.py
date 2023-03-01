#!/usr/bin/python3
# The main code of the Simulator

from CloudDefrag.Misc.misc import *
from stable_baselines3.common.env_checker import check_env
import gym


# TODO: Improve Network Visualization
# max_hops_for_connectivity tau


def main():
    """
    Run the main program
    """

    train_model = True
    test_model = not train_model

    # Frag. settings
    max_hops_for_connectivity = 2

    # #Test DQN Env
    game = VNFEnv(max_hops_for_connectivity=max_hops_for_connectivity)
    agent = Agent_BS3(game)



    # It will check your custom environment and output additional warnings if needed
    check_env(game)



    if train_model:
        train_BS3(game, agent)
        print("Done Training")

    if test_model:
        # Load Trained Model
        trained_model_folder_path = './output/DQN/model/model.pth'
        trained_model = Linear_QNet(game.state_vector_size, 256, game.action_space_size)
        trained_model.load_state_dict(torch.load(trained_model_folder_path))
        test_dqn_model(trained_model, max_hops_for_connectivity)

if __name__ == '__main__':
    main()
