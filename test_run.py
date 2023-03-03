#!/usr/bin/python3
# The main code of the Simulator

from CloudDefrag.Misc.misc import *

from stable_baselines3 import A2C


def main():
    """
    Run the main program
    """

    train_model = True
    test_model = not train_model

    # Frag. settings
    max_hops_for_connectivity = 2

    # #Test DQN Env
    env = VNFEnv(max_hops_for_connectivity=max_hops_for_connectivity)
    agent = Agent_BS3(env)

    if train_model:
        models_dir = f"output/RL/models/{int(time.time())}/"
        logdir = f"output/RL/logs/{int(time.time())}/"

        if not os.path.exists(models_dir):
            os.makedirs(models_dir)

        if not os.path.exists(logdir):
            os.makedirs(logdir)

        model = A2C('MlpPolicy', env, verbose=0, tensorboard_log=logdir)

        TIMESTEPS = 50000
        iters = 0
        for i in range(1):
            iters += 1
            model.learn(total_timesteps=TIMESTEPS, reset_num_timesteps=False, tb_log_name=f"A2C_2")
            model.save(f"{models_dir}/{TIMESTEPS * iters}")

        print("Done Training")

    # if test_model:
    #
    #     # Load Trained Model
    #     # trained_model_folder_path = './output/DQN/model/model.pth'
    #     # trained_model = Linear_QNet(game.state_vector_size, 256, game.action_space_size)
    #     # trained_model.load_state_dict(torch.load(trained_model_folder_path))
    #     # test_dqn_model(trained_model, max_hops_for_connectivity)


if __name__ == '__main__':
    main()
