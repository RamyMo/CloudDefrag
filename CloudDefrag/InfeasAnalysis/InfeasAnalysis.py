import multiprocessing
import sys
import gurobipy as gp
from gurobipy import GRB
from gurobipy.gurobipy import Model
import numpy as np
import scipy.sparse as sp
import time
import re
from CloudDefrag.InfeasAnalysis.iis import IISGraph, IISCompute
from CloudDefrag.InfeasAnalysis.iis.IISCover import IISCover
from CloudDefrag.InfeasAnalysis.iis.ModelLib import AdvancedModel
from CloudDefrag.InfeasAnalysis.iis.Chinneck import IISFinder, IISesFinder, IISRelaxer
from CloudDefrag.InfeasAnalysis.iis.RepairResult import RepairResult


def filtering(model, maxExecutionTime, maxNumOfCoversToShow, methodOfIISRelaxation):
    start_time = time.time()
    modifiableConstraints = []  # List of modif. constrs names
    IISCompute.findModifConstrs(model, modifiableConstraints)

    IISCovers = []  # Hold IIS covers in strings form
    while (time.time() - start_time) <= maxExecutionTime:
        subModel = model.copy()  # Create a copy of the model
        currentIISCover = IISCompute.findIISCoverVNF(subModel, IISCovers, modifiableConstraints,
                                                     methodOfIISRelaxation)  # for vnf problem
        if currentIISCover:
            IISCovers.append(currentIISCover)
        if methodOfIISRelaxation == "CostBased":  # Run one time only for CostBased method
            break

    minIISCovers = IISCompute.minIISCovers(IISCovers)
    IISCovers = []  # Now IISCovers will hold the IIScovers as objects of IISCover Class

    for i in minIISCovers:
        IISCovers.append(IISCover(model, i))

    IISCovers.sort(key=lambda x: x.resourcesCostEst, reverse=False)  # Sort ISSCovers based on resourcesCostEst

    print(f"\t\t\t *** Showing the best {maxNumOfCoversToShow} IIS covers out of {len(minIISCovers)} ***")
    j = 0
    for i in IISCovers:
        print(i.constraints)
        print("Cost:", i.resourcesCostEst, "Number of servers:", i.numOfServersUsed, "Num of Changes:",
              i.numOfConstraints)
        print("")
        j += 1
        if j >= maxNumOfCoversToShow:
            break
    exec_time = time.time() - start_time
    print("Execution Time: %s seconds" % exec_time)


def enum(model):
    start_time = time.time()
    maxRunTime = 100
    modifiableConstraints = []  # List of modif. constrs names
    IISCompute.findModifConstrs(model, modifiableConstraints)

    constraintsDictionary = {}
    constraints = []  # List of modif. constrs indices
    for c in model.getConstrs():
        constraintsDictionary[c.ConstrName] = c.index
        if c.ConstrName in modifiableConstraints:
            constraints.append(c.index)  # constraints will be only the modifiable constrs

    constraintsPowerSet = list(IISGraph.powerset(constraints))
    print("Number of Modifiable Constraints: ", len(constraints))
    print("Number of sets in the powerset: ", len(constraintsPowerSet))
    IISes = []
    while True:
        subModel = model.copy()
        IIS = IISGraph.shrink(subModel, constraintsPowerSet, constraints, constraintsDictionary, IISes)
        if len(IIS) != 0:
            IISes.append(IIS)
        if len(constraintsPowerSet) == 0:
            break

        exec_time = time.time() - start_time
        if exec_time >= maxRunTime:
            break
    exec_time = time.time() - start_time

    universe = set()

    ISSesConstr = []
    for IIS in IISes:
        universe = universe.union(set(IIS))
        IISConstr = []
        for c in IIS:
            IISConstr.append(model.getConstrs()[c])
        ISSesConstr.append(IISConstr)

    minCover = IISCompute.set_cover(universe, IISes)
    print("Number of IISes = ", len(IISes))
    # print(IISes)
    # print(ISSesConstr)
    n = len(IISes)
    m = len(universe)

    # print("Min Cover is ", minCover)
    print("Number of sets = ", n)
    print("Size of universe = ", m)

    exec_time = time.time() - start_time
    print("Execution Time: %s seconds" % exec_time)


def filteringShuffle(model):
    start_time = time.time()
    iisesFinder = IISesFinder(model)
    iisesFinder.setMaxShuffles(8)
    iisesFinder.setMaxNumOfProcesses(5)
    IISes = iisesFinder.findIISesParallel()  # Find Initial IISes

    shuffle_exec_time = time.time() - start_time
    # iisesFinder.printIISes()

    iisesRelaxer = IISRelaxer(model, IISes)
    iisesRelaxer.findIISesConstraints()
    # iisesRelaxer.printIISesConstraints()
    # iisesRelaxer.relaxToFeasbilityGurobi()
    iisesRelaxer.relaxToFeasbilityLoop()
    iisCover = iisesRelaxer.IISCover

    print("\t\t*** Result Summary ***")
    print("Cover is: ", iisCover.constraints)
    print("Cost:", iisCover.resourcesCostEst, "Number of servers:", iisCover.numOfServersUsed, "Num of Changes:",
          iisCover.numOfConstraints)
    exec_time = time.time() - start_time

    print("Execution Time for initial IISes = %s seconds" % shuffle_exec_time)
    print("Execution Time for finding the repair = %s seconds" % (exec_time - shuffle_exec_time))
    print("Execution Time: %s seconds" % exec_time)


def filteringShuffleCover(model):
    start_time = time.time()
    iisesFinder = IISesFinder(model)
    iisesFinder.setMaxShuffles(8)
    iisesFinder.setMaxNumOfProcesses(8)
    IISes = iisesFinder.findIISesParallel()  # Find Initial IISes

    shuffle_exec_time = time.time() - start_time
    # iisesFinder.printIISes()

    iisesRelaxer = IISRelaxer(model, IISes)
    iisesRelaxer.findIISesConstraints()
    iisesRelaxer.relaxToFeasbilityLoopCover()
    iisCover = iisesRelaxer.IISCover

    print("\t\t*** Result Summary ***")
    print("Cover is: ", iisCover.constraints)
    print("Cost:", iisCover.resourcesCostEst, "Number of servers:", iisCover.numOfServersUsed, "Num of Changes:",
          iisCover.numOfConstraints)
    exec_time = time.time() - start_time

    print("Execution Time for initial IISes = %s seconds" % shuffle_exec_time)
    print("Execution Time for finding the repair = %s seconds" % (exec_time - shuffle_exec_time))
    print("Execution Time: %s seconds" % exec_time)


def elasticHeur(model, all_constrs_are_modif, recommended_consts_groups_to_relax) -> RepairResult:
    # https://www.gurobi.com/documentation/9.5/refman/py_model_feasrelax.html#pythonmethod:Model.feasRelax
    # print("\nAlgorithm is Elastic Heuristic\n ")
    isRepaired = False
    start_time = time.time()
    relax_C1 = True if "C1" in recommended_consts_groups_to_relax else False
    relax_C2 = True if "C2" in recommended_consts_groups_to_relax else False
    relax_C3 = True if "C3" in recommended_consts_groups_to_relax else False
    relax_C4 = True if "C4" in recommended_consts_groups_to_relax else False

    # TODO Add a RL agent that will recommend the violConstrs

    violConstrs = []
    rhspen = []
    for c in model.getConstrs():
        if all_constrs_are_modif:
            violConstrs.append(c)
            rhspen.append(1000)
            continue
        elif "C1" in c.ConstrName and "cpu" in c.ConstrName and relax_C1:
            violConstrs.append(c)
            rhspen.append(1)
        elif "C1" in c.ConstrName and "memory" in c.ConstrName and relax_C1:
            violConstrs.append(c)
            rhspen.append(1)
        elif "C1" in c.ConstrName and "storage" in c.ConstrName and relax_C1:
            violConstrs.append(c)
            rhspen.append(1 / 100)
        elif "C2" in c.ConstrName and relax_C2:
            violConstrs.append(c)
            rhspen.append(1 / 100)
        elif "C3" in c.ConstrName and relax_C3:
            violConstrs.append(c)
            rhspen.append(1000)
        elif "C4" in c.ConstrName and relax_C4:
            violConstrs.append(c)
            rhspen.append(1000000)

        # else:
        #     violConstrs.append(c)
        #     rhspen.append(100000)

    model.optimize()
    model.feasRelax(0, False, None, None, None, violConstrs, rhspen)
    model.optimize()
    isRepaired = IISCompute.isFeasible(model)
    cost = 0
    # print("\nElastic Variables:")
    if isRepaired:
        for var in model.getVars():
            if "Art" in var.VarName:
                if var.X != 0:
                    # print(var.VarName, " : ", var.X)
                    if "cpu" in var.VarName:
                        cost += var.X
                    elif "memory" in var.VarName:
                        cost += var.X
                    elif "storage" in var.VarName:
                        cost += var.X / 100
                    elif "bw_cap" in var.VarName:
                        cost += var.X / 100
                    else:
                        cost += var.X  # BW
    else:
        cost = -1000

    # print("\n\t\t*** Result Summary ***")
    # print("Cost:", cost, "Number of servers:", "Num of Changes:")

    exec_time = time.time() - start_time
    # print("Repair Execution Time: %s seconds" % exec_time)
    result = RepairResult(model, cost, exec_time, "Elastic Heuristic", recommended_consts_groups_to_relax, isRepaired)
    return result

def get_model_statistics(model):
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


class InfeasAnalyzer:
    def __init__(self, model, **kwargs) -> None:
        # print("\n \t\t*** Printing Model Info. for Inf. Analysis ***")
        # print("Number of Constraints = ", len(model.getConstrs()))
        # print("Number of Variables = ", len(model.getVars()))
        self._algorithm = kwargs["algorithm"] if "algorithm" in kwargs else "ElasticHeur"
        self._model = model
        self._RepairResult = None
        # get_model_statistics(model)

    @property
    def algorithm(self):
        return self._algorithm

    @algorithm.setter
    def algorithm(self, value):
        self._algorithm = value

    @property
    def result(self):
        return self._RepairResult

    def repair_infeas(self, **kwargs):
        self.algorithm = kwargs["algorithm"] if "algorithm" in kwargs else "ElasticHeur"
        # algorithm = "ElasticHeur"  # Algorithm used to find IISes: "Filtering", "FilteringShuffle","FilteringShuffleCover" "Enum", "Pivoting", "ElasticHeur" (In Progress)
        model = self._model
        all_constrs_are_modif = kwargs["all_constrs_are_modif"] if "all_constrs_are_modif" in kwargs else False
        recommended_consts_groups_to_relax = kwargs["recommeded_consts_groups_to_relax"] if \
            "recommeded_consts_groups_to_relax" in kwargs else "C1, C2, C3, C4"

        if self.algorithm == "Filtering":
            maxExecutionTime = 10  # Maximum time to run (in seconds)
            maxNumOfCoversToShow = 3  # Maximum number of IIS Covers to print at the end
            methodOfIISRelaxation = "CostBased"  # How to relax the IIS, methods: "Random", "ServerGrouping", "CostBased": needs to run one time
            filtering(model, maxExecutionTime, maxNumOfCoversToShow, methodOfIISRelaxation)
        elif self.algorithm == "Enum":
            enum(model)
        elif self.algorithm == "FilteringShuffle":
            filteringShuffle(model)
        elif self.algorithm == "FilteringShuffleCover":
            filteringShuffleCover(model)
        elif self.algorithm == "ElasticHeur":
            self._RepairResult = elasticHeur(model, all_constrs_are_modif, recommended_consts_groups_to_relax)
