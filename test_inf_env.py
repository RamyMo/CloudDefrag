from CloudDefrag.QLearning.Inf_Env import Inf_Env
import gurobipy as gp
env = Inf_Env("output/RamyILP Model.lp")
result = env.evaluate((1,1,0,0))
