import gurobipy as gp
from gurobipy import GRB
from gurobipy.gurobipy import Model

new_model = gp.read("output/repaired-model.lp")

#https://www.gurobi.com/documentation/9.5/refman/presolve.html
new_model.setParam("Presolve", 2)

new_model.optimize()