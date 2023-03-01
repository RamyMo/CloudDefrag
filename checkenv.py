#!/usr/bin/python3
from CloudDefrag.Misc.misc import *
from stable_baselines3.common.env_checker import check_env


def checkenv():
    """Creates a custom environment and an agent to interact with it, then checks the environment to ensure that it meets
        the necessary requirements.

        Args:
            None.

        Returns:
            None.
        """
    # Frag. settings
    max_hops_for_connectivity = 2
    # Test Env
    env = VNFEnv(max_hops_for_connectivity=max_hops_for_connectivity)
    # It will check your custom environment and output additional warnings if needed
    check_env(env)
    print("Check PASSED! The VNFEnv environment follows the gym interface!")


if __name__ == '__main__':
    checkenv()
