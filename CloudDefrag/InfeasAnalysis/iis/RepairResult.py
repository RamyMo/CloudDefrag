import gurobipy as gp
from gurobipy import GRB
from gurobipy.gurobipy import Model
import numpy as np


class RepairResult:

    def __init__(self, model, repair_cost, repair_exec_time, algorithm, recommended_consts_groups_to_relax, isRepaired)\
            -> None:
        self._isRepaired = isRepaired
        self._model = model
        self._repair_cost = repair_cost
        self._repair_exec_time = repair_exec_time
        self._algorithm = algorithm
        self._recommended_consts_groups_to_relax =recommended_consts_groups_to_relax

    @property
    def repair_cost(self):
        return self._repair_cost

    @property
    def repair_exec_time(self):
        return self._repair_exec_time

    @property
    def algorithm(self):
        return self._algorithm

    @property
    def recommended_consts_groups_to_relax(self):
        return self._recommended_consts_groups_to_relax

    def print_model_statistics(self):
        model = self._model
        num_of_constrs = len(model.getConstrs())
        c1 = 0
        c2 = 0
        c3 = 0
        c4 = 0
        c5 = 0
        c6 = 0
        c7 = 0
        c8 = 0
        for c in model.getConstrs():
            if "C1" in c.ConstrName:
                c1 += 1
            elif "C2" in c.ConstrName:
                c2 += 1
            elif "C3" in c.ConstrName:
                c3 += 1
            elif "C4" in c.ConstrName:
                c4 += 1
            elif "C5" in c.ConstrName:
                c5 += 1
            elif "C6" in c.ConstrName:
                c6 += 1
            elif "C7" in c.ConstrName:
                c7 += 1
            elif "C8" in c.ConstrName:
                c8 += 1

        print("C1 is {:0.2f} % of all constrs".format((c1 / num_of_constrs) * 100))
        print("C2 is {:0.2f} % of all constrs".format((c2 / num_of_constrs) * 100))
        print("C3 is {:0.2f} % of all constrs".format((c3 / num_of_constrs) * 100))
        print("C4 is {:0.2f} % of all constrs".format((c4 / num_of_constrs) * 100))
        print("C5 is {:0.2f} % of all constrs".format((c5 / num_of_constrs) * 100))
        print("C6 is {:0.2f} % of all constrs".format((c6 / num_of_constrs) * 100))
        print("C7 is {:0.2f} % of all constrs".format((c7 / num_of_constrs) * 100))
        print("C8 is {:0.2f} % of all constrs".format((c8 / num_of_constrs) * 100))

    def print_model_info(self):
        model = self._model
        print("\n \t\t*** Printing Model Info. for Inf. Analysis ***")
        print("Number of Constraints = ", len(model.getConstrs()))
        print("Number of Variables = ", len(model.getVars()))
        self.print_model_statistics()

    def print_elastic_variables(self):
        model = self._model
        print("\nElastic Variables:")
        for var in model.getVars():
            if "Art" in var.VarName:
                if var.X != 0:
                    print(var.VarName, " : ", var.X)

    def print_result_summary(self):
        cost = self.repair_cost
        print("\n\t\t*** Result Summary ***")
        print("Cost:", cost, "Number of servers:", "Num of Changes:")
        exec_time = self.repair_exec_time
        print("Repair Execution Time: %s seconds" % exec_time)

    def print_result(self):
        self.print_model_info()
        print(f"\nAlgorithm is {self.algorithm}\n")
        print(f"Recommended Constrs to relax: {self.recommended_consts_groups_to_relax}")
        if self._isRepaired:
            self.print_elastic_variables()
            self.print_result_summary()
        else:
            print("\nCould not repair the infeasibility!\n")
            self.print_result_summary()

