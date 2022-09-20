import gurobipy as gp
from gurobipy import GRB
from gurobipy.gurobipy import Model
from CloudDefrag.InfeasAnalysis.InfeasAnalysis import InfeasAnalyzer
from CloudDefrag.InfeasAnalysis.iis import IISCompute
from CloudDefrag.InfeasAnalysis.iis.RepairResult import RepairResult
from CloudDefrag.QLearning.Inf_Env import Inf_Env
from CloudDefrag.QLearning.Qlearning import Qlearning
import numpy as np
import time




# Read from table
# q_table = np.load(f"output/Q-tables/20-qtable.npy")
#
# print("   ")

# Train

model = gp.read("output/RamyILP Model.lp")
isfeasible = IISCompute.isFeasible(model)
if isfeasible:
    print("Model is feasible")
else:
    print("Model verified to be infeasible")
    env = Inf_Env("output/RamyILP Model.lp")
    qlearn = Qlearning(env)
    start_time = time.time()
    qlearn.learn()
    learning_time = time.time() - start_time
    print(f"\nLearning time is: {learning_time} seconds")
    # qlearn.plot()
    # qlearn.generate_qtables_charts()
    # qlearn.generate_qtables_video()

    print("   ")


    # Analyze repair
    # print("Waiting for result ...")
    # inf_analyzer = InfeasAnalyzer(model)
    # inf_analyzer.repair_infeas(all_constrs_are_modif=False, recommeded_consts_groups_to_relax="C1, C2, C3, C4")
    # repair_result = inf_analyzer.result
    # repair_result.print_result()
