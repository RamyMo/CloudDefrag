import gurobipy as gp
from gurobipy import GRB
from gurobipy.gurobipy import Model
import numpy as np


class RepairResult:

    def __init__(self, model, repair_cost, repair_exec_time, algorithm, recommended_consts_groups_to_relax, isRepaired,
                 violConstrs, constraints_grouping_method)-> None:
        self._violConstrs = violConstrs
        self._isRepaired = isRepaired
        self._model = model
        self._repair_cost = repair_cost
        self._repair_exec_time = repair_exec_time
        self._algorithm = algorithm
        self._recommended_consts_groups_to_relax =recommended_consts_groups_to_relax
        self._constraints_grouping_method = constraints_grouping_method
        self._selected_consts_groups_to_relax = self.get_selected_consts_location_groups_to_relax()

    @property
    def violable_Constrs(self):
        return self._violConstrs
    @property
    def number_of_violable_constrs(self):
        return len(self._violConstrs)

    @property
    def repaired_model(self):
        return self._model

    @property
    def is_repaired(self):
        return self._isRepaired

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

    @property
    def selected_consts_groups_to_relax(self):
        return self._selected_consts_groups_to_relax

    @selected_consts_groups_to_relax.setter
    def selected_consts_groups_to_relax(self, value):
        self._selected_consts_groups_to_relax = value

    @property
    def constraints_grouping_method(self):
        return self._constraints_grouping_method

    @constraints_grouping_method.setter
    def constraints_grouping_method(self, value):
        self._constraints_grouping_method = value

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

    def get_selected_consts_location_groups_to_relax(self):
        constraints_grouping_method = self._constraints_grouping_method
        if constraints_grouping_method == "Resource_Location":
            if self._isRepaired:
                model = self._model
                selected_groups = []
                for var in model.getVars():
                    if "Art" in var.VarName:
                        if var.X != 0:
                            group = get_constraint_location_group(var.VarName)
                            if group not in selected_groups:
                                selected_groups.append(group)
                return selected_groups
            else:
                return None
        elif constraints_grouping_method == "Constraint_Type":
            if self._isRepaired:
                model = self._model
                selected_groups = []
                for var in model.getVars():
                    if "Art" in var.VarName:
                        if var.X != 0:
                            if "C1" in var.VarName and "C1" not in selected_groups:
                                selected_groups.append("C1")
                            elif "C2" in var.VarName and "C2" not in selected_groups:
                                selected_groups.append("C2")
                            elif "C3" in var.VarName and "C3" not in selected_groups:
                                selected_groups.append("C3")
                            elif "C4" in var.VarName and "C4" not in selected_groups:
                                selected_groups.append("C4")
                return selected_groups
            else:
                return None

    def print_result_summary(self):
        cost = self.repair_cost
        print("\t\t*** Repair Result Summary ***")
        print(f"Number of Vilable Constraints: {self.number_of_violable_constrs}")
        print("Cost:", cost, "Number of servers:", "Num of Changes:")
        exec_time = self.repair_exec_time
        print("Repair Execution Time: %s seconds" % exec_time)

    def print_result(self, **kwargs):
        show_elastic_variables = kwargs["show_elastic_variables"] if "show_elastic_variables" in kwargs else False
        show_model_info = kwargs["show_model_info"] if "show_model_info" in kwargs else False
        if show_model_info:
            self.print_model_info()
        print(f"Fixing Infeasibility using {self.algorithm}...")
        print(f"Recommended Constrs to relax: {self.recommended_consts_groups_to_relax}")
        print(f"Selected Constrs to relax: {self.selected_consts_groups_to_relax}")
        if self._isRepaired:
            if show_elastic_variables:
                self.print_elastic_variables()
            self.print_result_summary()

        else:
            print("\nCould not repair the infeasibility!\n")
            self.print_result_summary()


def get_constraint_location_group(ConstrName):
    # Define how network is divided into locations. Follow Diagram in 12-10-2022 Group Meeting Presentation
    Location_Group = ""
    L1_matches = ["w3", "s3", "s4"]
    L2_matches = ["w2", "s8"]
    L3_matches = ["s1", "s2", "s5", "s6", "s7", "w1"]
    L4_matches = ["w6"]
    L5_matches = ["s9", "s10", "s11", "w7", "w8", "w4", "w5"]

    if any(x in ConstrName for x in L1_matches):
        Location_Group = "L1"
    elif any(x in ConstrName for x in L2_matches):
        Location_Group = "L2"
    elif any(x in ConstrName for x in L3_matches):
        Location_Group = "L3"
    elif any(x in ConstrName for x in L4_matches):
        Location_Group = "L4"
    elif any(x in ConstrName for x in L5_matches):
        Location_Group = "L5"

    return Location_Group
