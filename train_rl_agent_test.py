import gurobipy as gp
from gurobipy import GRB
from gurobipy.gurobipy import Model
from CloudDefrag.InfeasAnalysis.InfeasAnalysis import InfeasAnalyzer
from CloudDefrag.InfeasAnalysis.iis import IISCompute
from CloudDefrag.InfeasAnalysis.iis.RepairResult import RepairResult
from CloudDefrag.QLearning.Inf_Env import Inf_Env, Inf_Env_Location
from CloudDefrag.QLearning.Qlearning import Qlearning
import tracemalloc
import numpy as np
import time




# Read from table
# q_table = np.load(f"output/Q-tables/20-qtable.npy")
#
# print("   ")

# Train

tracemalloc.start()

network_nodes_file = "input/ReducedTopo/01-NetworkNodes.csv"
network_connections_file = "input/ReducedTopo/02-NetworkConnections.csv"
agent_gateway = "w3"
env = Inf_Env_Location(network_nodes_file, network_connections_file, agent_gateway)
qlearn = Qlearning(env)
start_time = time.time()
qlearn.learn()
learning_time = time.time() - start_time
print(f"\nLearning time is: {learning_time} seconds")
qlearn.plot()

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

print("[ Top 10 ] after training ")
for stat in top_stats[:10]:
    print(stat)

# for i in range(60):
#     snapshot1 = tracemalloc.take_snapshot()
#     time.sleep(1)
#     snapshot2 = tracemalloc.take_snapshot()
#     stats = snapshot2.compare_to(snapshot1, 'lineno')
#     print(f"After {i+1} seconds of training")
#     for stat in stats[:10]:
#         print(stat)

# qlearn.generate_qtables_charts()
# qlearn.generate_qtables_video()


# Analyze repair
# print("Waiting for result ...")
# inf_analyzer = InfeasAnalyzer(model)
# inf_analyzer.repair_infeas(all_constrs_are_modif=False, recommeded_consts_groups_to_relax="C1, C2, C3, C4")
# repair_result = inf_analyzer.result
# repair_result.print_result()
