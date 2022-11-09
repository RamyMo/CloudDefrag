import multiprocessing
import sys
from typing import List

import gurobipy as gp
from gurobipy import GRB
from gurobipy.gurobipy import Model
import numpy as np
import time
import re
from CloudDefrag.InfeasAnalysis.iis import IISGraph, IISCompute
from CloudDefrag.InfeasAnalysis.iis.IISCover import IISCover
from CloudDefrag.InfeasAnalysis.iis.ModelLib import AdvancedModel
from CloudDefrag.InfeasAnalysis.iis.Chinneck import IISFinder, IISesFinder, IISRelaxer
from CloudDefrag.InfeasAnalysis.iis.RepairResult import RepairResult
from CloudDefrag.Logging.Logger import Logger
from CloudDefrag.Model.Algorithm.Request import NewVMRequest, HostedVMRequest
from CloudDefrag.Model.Graph.Link import LinkSpecs, VirtualLink
from CloudDefrag.Model.Graph.Network import PhysicalNetwork


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


def elasticHeur(model, all_constrs_are_modif, constraints_grouping_method,
                recommended_consts_groups_to_relax, infeas_analyzer_instance) -> RepairResult:
    # https://www.gurobi.com/documentation/9.5/refman/py_model_feasrelax.html#pythonmethod:Model.feasRelax
    # print("\nAlgorithm is Elastic Heuristic\n ")
    isRepaired = False
    if "Constraint_Type" in constraints_grouping_method:
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
                rhspen.append(1 / 10)
            elif "C3" in c.ConstrName and relax_C3:
                violConstrs.append(c)
                rhspen.append(1000000)
            elif "C4" in c.ConstrName and relax_C4:
                violConstrs.append(c)
                rhspen.append(1000000)

            # else:
            #     violConstrs.append(c)
            #     rhspen.append(100000)
    elif "Resource_Location" in constraints_grouping_method:
        start_time = time.time()
        violConstrs = []
        rhspen = []
        for c in model.getConstrs():
            location_group = get_constraint_location_group(c.ConstrName)
            if all_constrs_are_modif:
                violConstrs.append(c)
                rhspen.append(1000)
                continue
            if location_group in recommended_consts_groups_to_relax:
                if "C1" in c.ConstrName and "cpu" in c.ConstrName:
                    violConstrs.append(c)
                    rhspen.append(1)
                elif "C1" in c.ConstrName and "memory" in c.ConstrName:
                    violConstrs.append(c)
                    rhspen.append(1)
                elif "C1" in c.ConstrName and "storage" in c.ConstrName:
                    violConstrs.append(c)
                    rhspen.append(1 / 100)
                elif "C2" in c.ConstrName:
                    violConstrs.append(c)
                    rhspen.append(1 / 10)
                # Todo: Fix: Resource_Location doesn't take into account relaxing C3 or C4

                # elif "C3" in c.ConstrName:
                #     violConstrs.append(c)
                #     rhspen.append(1000000)
                # elif "C4" in c.ConstrName:
                #     violConstrs.append(c)
                #     rhspen.append(1000000)

            else:
                continue
            # else:
            #     violConstrs.append(c)
            #     rhspen.append(100000)

    # model.optimize()
    model.feasRelax(0, False, None, None, None, violConstrs, rhspen)

    # Set Artificial variables limits by adding constrs
    for c in violConstrs:
        limit = get_resource_upgrade_limit(c,
                                           compute_resource_factor=infeas_analyzer_instance.compute_resource_factor,
                                           bw_factor=infeas_analyzer_instance.bw_factor,
                                           e2e_delay_factor=infeas_analyzer_instance.e2e_delay_factor,
                                           propg_delay_factor=infeas_analyzer_instance.propg_delay_factor)
        var = model.getVarByName(f"ArtN_{c.ConstrName}")
        model.addConstr(var <= limit, name=f"ArtN_{c.ConstrName}_limit")

    # Save repaired model for inspection
    model.write(f'output/repaired-model.lp')

    # https://www.gurobi.com/documentation/9.5/refman/presolve.html
    # Set Presolve to 2 to fix the problem of solver giving a zero solution
    # A value of -1 corresponds to an automatic setting. Other options are off (0), conservative (1), or aggressive (2). More aggressive application of presolve takes more time, but can sometimes lead to a significantly tighter model.
    # TODO: Fix: Solution count problem still exist. Solver finds multiple solutions and return the wrong one.
    model.setParam("Presolve", 2)

    model.optimize()

    isRepaired = IISCompute.isFeasible(model)
    cost = 0
    # print("\nElastic Variables:")
    if isRepaired:
        for var in model.getVars():
            if "Art" in var.VarName:
                if var.X != 0:
                    # print(var.VarName, " : ", var.X)
                    if "C1" in var.VarName:
                        if "cpu" in var.VarName:
                            cost += var.X  # 1 cpu core is one unit of cost
                        elif "memory" in var.VarName:
                            cost += var.X  # 1 GB of memory is one unit of cost
                        elif "storage" in var.VarName:
                            cost += var.X / 100  # 100 GB of storage is one unit of cost
                    elif "C2" in var.VarName:
                        cost += var.X / 10  # 10 Mbps of BW is one unit of cost
                    elif "C3" in var.VarName:
                        cost += var.X * 10 ** 6  # 1 µs of extra delay is one unit of cost
                    elif "C4" in var.VarName:
                        cost += var.X * 10 ** 6  # 1 µs of extra delay is one unit of cost
    else:
        cost = -1000

    # print("\n\t\t*** Result Summary ***")
    # print("Cost:", cost, "Number of servers:", "Num of Changes:")

    exec_time = time.time() - start_time
    # print("Repair Execution Time: %s seconds" % exec_time)
    result = RepairResult(model, cost, exec_time, "Elastic Heuristic", recommended_consts_groups_to_relax, isRepaired,
                          violConstrs, constraints_grouping_method)
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


def get_resource_upgrade_limit(c, compute_resource_factor, bw_factor, e2e_delay_factor, propg_delay_factor):
    limit = None
    if "C1" in c.ConstrName and "cpu" in c.ConstrName:
        limit = 1 * compute_resource_factor
    elif "C1" in c.ConstrName and "memory" in c.ConstrName:
        limit = 1 * compute_resource_factor
    elif "C1" in c.ConstrName and "storage" in c.ConstrName:
        limit = 100 * compute_resource_factor
    elif "C2" in c.ConstrName:
        limit = 100 * bw_factor
    elif "C3" in c.ConstrName:
        limit = (10 ** -3) * e2e_delay_factor
    elif "C4" in c.ConstrName:
        limit = (10 ** -6) * propg_delay_factor
    return limit


class InfeasAnalyzer:
    def __init__(self, model, **kwargs) -> None:
        # print("\n \t\t*** Printing Model Info. for Inf. Analysis ***")
        # print("Number of Constraints = ", len(model.getConstrs()))
        # print("Number of Variables = ", len(model.getVars()))
        self._algorithm = kwargs["algorithm"] if "algorithm" in kwargs else "ElasticHeur"
        self._model = model
        self._RepairResult = None
        self._compute_resource_factor = kwargs[
            "compute_resource_factor"] if "compute_resource_factor" in kwargs else 100
        self._bw_factor = kwargs["bw_factor"] if "bw_factor" in kwargs else 40
        self._e2e_delay_factor = kwargs["e2e_delay_factor"] if "e2e_delay_factor" in kwargs else 5
        self._propg_delay_factor = kwargs["propg_delay_factor"] if "propg_delay_factor" in kwargs else 10
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

    @property
    def compute_resource_factor(self):
        return self._compute_resource_factor

    @compute_resource_factor.setter
    def compute_resource_factor(self, value):
        self._compute_resource_factor = value

    @property
    def bw_factor(self):
        return self._bw_factor

    @bw_factor.setter
    def bw_factor(self, value):
        self._bw_factor = value

    @property
    def e2e_delay_factor(self):
        return self._e2e_delay_factor

    @e2e_delay_factor.setter
    def e2e_delay_factor(self, value):
        self._e2e_delay_factor = value

    @property
    def propg_delay_factor(self):
        return self._propg_delay_factor

    @propg_delay_factor.setter
    def propg_delay_factor(self, value):
        self._propg_delay_factor = value
    def repair_infeas(self, **kwargs):
        constraints_grouping_method = kwargs[
            "constraints_grouping_method"] if "constraints_grouping_method" in kwargs else "Constraint_Type"
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
            self._RepairResult = elasticHeur(model, all_constrs_are_modif, constraints_grouping_method,
                                             recommended_consts_groups_to_relax,
                                             infeas_analyzer_instance=self)

    def apply_infeas_repair(self, net: PhysicalNetwork, hosted_requests: List[HostedVMRequest],
                            new_requests: List[NewVMRequest]):
        repair_result = self.result
        repaired_model = repair_result.repaired_model
        for var in repaired_model.getVars():
            if "Art" in var.VarName:
                if var.X != 0:
                    if "C1" in var.VarName:
                        server_name = re.search('C1_(.+?)_', var.VarName).group(1)
                        server = net.get_node_by_name(server_name)
                        server.is_selected_for_feas_repair = True
                        if "cpu" in var.VarName:
                            server.specs.increase_cpu_by(var.X)
                            server.repair_specs.increase_cpu_by(var.X)
                            Logger.log.info(f"Increased number of CPU cores of server {server_name} by {var.X} cores "
                                            f"new value is: {server.specs.cpu} cores")
                        elif "memory" in var.VarName:
                            server.specs.increase_memory_by(var.X)
                            server.repair_specs.increase_memory_by(var.X)
                            Logger.log.info(f"Increased memory of server {server_name} by {var.X} GB "
                                            f"new value is: {server.specs.memory} GB")
                        elif "storage" in var.VarName:
                            server.specs.increase_storage_by(var.X)
                            server.repair_specs.increase_storage_by(var.X)
                            Logger.log.info(f"Increased storage of server {server_name} by {var.X} GB "
                                            f"new value is: {server.specs.storage} GB")
                    elif "C2" in var.VarName:
                        link_name = re.search('C2_(.+?)_', var.VarName).group(1)
                        link = net.get_link_by_name(link_name)
                        link.is_selected_for_feas_repair = True
                        link.link_specs.increase_bandwidth_by(var.X)
                        link.link_repair_specs.increase_bandwidth_by(var.X)
                        Logger.log.info(f"Increased bandwidth of link {link_name} by {var.X} Mbps "
                                        f"new value is: {link.link_specs.bandwidth} Mbps")
                    elif "C3" in var.VarName:
                        req_number = re.search('req(.+?)_', var.VarName).group(1)
                        req_index = int(req_number) - 1
                        is_new = True if "new" in var.VarName else False
                        if is_new:
                            request = new_requests[req_index]
                            request.is_selected_for_feas_repair = True
                            request.e2e_delay += var.X
                            request.extra_e2e_delay_repair += var.X
                            Logger.log.info(f"Increased the E2E delay requirement of new request No. {req_number} "
                                            f"by {var.X} µs "
                                            f"new value is: {request.e2e_delay} µs")
                        else:
                            request = hosted_requests[req_index]
                            request.is_selected_for_feas_repair = True
                            request.e2e_delay += var.X
                            request.extra_e2e_delay_repair += var.X
                            Logger.log.info(
                                f"Increased the E2E delay requirement of hosted request No. {req_number} by {var.X} µs "
                                f"new value is: {request.e2e_delay} µs")
                    elif "C4" in var.VarName:
                        req_number = re.search('req(.+?)_', var.VarName).group(1)
                        req_index = int(req_number) - 1
                        is_new = True if "new" in var.VarName else False
                        link_name = re.search('vlink_(.+?)_prop_delay', var.VarName).group(1)

                        if is_new:
                            request = new_requests[req_index]
                            request.is_selected_for_feas_repair = True
                            vlink = request.requested_vlinks_dict[link_name]
                            vlink.link_specs.increase_propagation_delay_by(var.X)
                            request.extra_prop_delay_per_link_repair_dict[vlink] = var.X

                            Logger.log.info(
                                f"Increased the propagation delay requirement of new request No. {req_number} "
                                f"vLink {link_name} by {var.X} µs new value is: "
                                f"{vlink.link_specs.propagation_delay} µs")
                        else:
                            request = hosted_requests[req_index]
                            request.is_selected_for_feas_repair = True
                            vlink = request.hosted_vlinks_dict[link_name]
                            vlink.link_specs.increase_propagation_delay_by(var.X)
                            request.extra_prop_delay_per_link_repair_dict[vlink] = var.X
                            Logger.log.info(
                                f"Increased the propagation delay requirement of hosted request No. {req_number} "
                                f"vLink {link_name} by {var.X} µs new value is: "
                                f"{vlink.link_specs.propagation_delay} µs")
        return
