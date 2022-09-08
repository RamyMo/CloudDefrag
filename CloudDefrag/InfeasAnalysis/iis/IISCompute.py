from cmath import cos
from itertools import groupby
import gurobipy as gp
from gurobipy import GRB
from gurobipy.gurobipy import Model
from random import randrange
from random import shuffle
import time
import re



#Return one IIS (list of strings) using Gurobi computeIIS. 
def computeIIS(model: gp.Model):
    model.computeIIS()
    IIS = []
    for c in model.getConstrs():
        if(c.IISConstr == 1):
            # print (c.ConstrName)
            if "c4(n" in c.ConstrName:                        #Enable only if you want to include modifiable constrs only
                    IIS.append(c.ConstrName)
    return IIS

#Takes Gurobi model as an input and return True if model is feasible and False o.w
def isFeasible(model):
    isFeas = False
    #Current optimization status for the model. Status values are described in the Status Code section.
    # https://www.gurobi.com/documentation/9.5/refman/optimization_status_codes.html#sec:StatusCodes
    # print(model.Status)
    model.optimize()
    #Get  model Status
    status = model.Status
    #https://www.gurobi.com/documentation/9.5/refman/dualreductions.html#parameter:DualReductions
    if status == 4:                         #Model was proven to be either infeasible or unbounded. 
        model.Params.DualReductions = 0
        model.optimize()
        status = model.Status
    
    if status == 2 or status == 5:              #OPTIMAL or UNBOUNDED
        IIS = []
        isFeas = True

    elif status == 3:                           #Model was proven to be infeasible.
        isFeas = False

    return isFeas

#shuffleIIS a function takes IIS as an input and returns a copy of shuffled IIS list
def shuffleIIS(IIS):
    shuffledIIS = IIS.copy()
    shuffle(shuffledIIS)
    return shuffledIIS
    
#relaxIIS function takes IIS and RADNOMLY return the constraint to be relaxed 
def relaxIISrandom(IIS):
    return IIS[randrange(len(IIS))]

#relaxIIS function takes IIS and return the constraint to be relaxed (VNF specific)
#This method follow server grouping method: look to relax dsk and mem first before randomly pick a constraint
def relaxIISrandomServerGrouping(IIS):
    shuffledIIS = shuffleIIS(IIS)
    for c in shuffledIIS:
        if "dsk" in c:                #Note: This can leads to adding redundent resources to the same server: may limit the method from finding optimal
            return c
    for c in shuffledIIS:
        if "mem" in c:                #Note: This can leads to adding redundent resources to the same server: may limit the method from finding optimal
            return c
    return IIS[randrange(len(IIS))]

#relaxIISrandomCostBased function takes IIS and return the constraint to be relaxed (VNF specific)
#This method follow cost based and server grouping methods: First, will try to relax constraints of the last server used then:
# assign cost to each constraint, then sort and then relax based on that
def relaxIISCostBased(IIS, model, IISCover):
    if IISCover:
        lastServerUsedName = InfeasConstr.findConstrServerName(IISCover[-1]) 
        for c in IIS:
            if lastServerUsedName in c:
                return c
    constraints = []
    for c in IIS:
        constraints.append(InfeasConstr(model, c))
    constraints.sort(key=lambda x: x.resourcesCost , reverse=False)        #Sort ISSCovers based on resourcesCostEst+
    for c in constraints:
        if "dsk" in c.constraintName:
            return c.constraintName
    for c in constraints:
        if "mem" in c.constraintName:
            return c.constraintName
    for c in constraints:
        if "cpu" in c.constraintName:
            return c.constraintName

# isIISCoverUnique a function that returns True if IISCover is not in IISCovers
def isIISCoverUnique(IISCover, IISCovers):
    for i in IISCovers:
        if set(IISCover) == set(i):
            return False
    return True

# reduceIIS function that removes the unmodifiable constraints from an IIS
def reduceIIS(IIS, modifiableConstraints):
    IIScopy = IIS.copy()
    for c in IIScopy:
        if c not in modifiableConstraints:
            IIS.remove(c)

#findIISCoverGeneral function returns IIS Cover that is not in IISCovers (For General Problems)
def findIISCoverGeneral(model, IISCovers):
    
    if isFeasible(model) == True:
        print("Model was proven to be feasible.")
        return []

    IISCover = []
    while isFeasible(model) == False:
        IIS = computeIIS(model)
        if len(IIS) == 1:
            IISCover.append(IIS[0])
            model.remove(model.getConstrByName(IIS[0])) 
            model.update()
        else:
            #Relax
            relaxedConstraint = relaxIISrandom(IIS)
            IISCover.append(relaxedConstraint)
            model.remove(model.getConstrByName(relaxedConstraint)) 
            model.update()

    if isIISCoverUnique(IISCover, IISCovers):
        return IISCover
    else:
        return []

#findIISCoverVNF function returns IIS Cover that is not in repairs (for VNF problem)
def findIISCoverVNF(model, IISCovers, modifiableConstraints, methodOfIISRelaxation):
    if isFeasible(model) == True:
        print("Model was proven to be feasible.")
        return []
    IISCover = []
    while isFeasible(model) == False:
        IIS = computeIIS(model)                         #Compute IIS using Gurobi Method
        # print(IIS)
        reduceIIS(IIS, modifiableConstraints)           #Remove unmodifiable constraints
        if len(IIS) == 1:
            IISCover.append(IIS[0])
            model.remove(model.getConstrByName(IIS[0])) 
            model.update()
        else:
            #Relax
            #Find a constraint to relax from IIS (VIP part) based on methodOfIISRelaxation
            if methodOfIISRelaxation == "Random":
                relaxedConstraint = relaxIISrandom(IIS)
            elif methodOfIISRelaxation == "ServerGrouping":
                relaxedConstraint = relaxIISrandomServerGrouping(IIS) 
            elif methodOfIISRelaxation == "CostBased":
                relaxedConstraint = relaxIISCostBased(IIS, model, IISCover) 
            IISCover.append(relaxedConstraint)
            model.remove(model.getConstrByName(relaxedConstraint)) 
            model.update()
    if isIISCoverUnique(IISCover, IISCovers):
        return IISCover
    else:
        return []

# minIISCovers function that remove all IIS covers that are not minimum  (a cover that is superset of another cover is not minimum)
def minIISCovers(IISCovers):
    minIISCovers = IISCovers.copy()
    for i in IISCovers:
        for j in IISCovers:
            if set(i) == set(j):
                continue
            else:
                if set(i).issubset(set(j)) and j in minIISCovers:
                    minIISCovers.remove(j)
    return minIISCovers

# findModifConstrs function that returns the list of modifiable constrs
def findModifConstrs(model, modifiableConstraints):
    #Initialize modifiableConstraints
    for c in model.getConstrs():
        if "c4(n" in c.ConstrName:                              #That's how we choose the modifiable constrs
            modifiableConstraints.append(c.ConstrName)

def set_cover(universe, subsets):
    """Find a family of subsets that covers the universal set"""
    elements = set(e for s in subsets for e in s)
    # Check the subs'ets cover the universe
    if elements != universe:
        return None
    covered = set()
    cover = []
    # Greedily add the subsets with the most uncovered points
    while covered != elements:
        subset = max(subsets, key=lambda s: len(s - covered))
        cover.append(subset)
        covered |= subset
 
    return cover
    
class InfeasConstr:
    def __init__(self, model, constraintName) -> None:
        self.model = model
        self.constraintName = constraintName
        self.RHS = model.getConstrByName(constraintName).RHS
        self.LHS = InfeasConstr.calcLHS(model,constraintName)
        self.diff = abs(self.RHS - self.LHS)
        self.serverName = InfeasConstr.findConstrServerName(constraintName)
        self.resourceType = InfeasConstr.findConstrResourceType(constraintName) 
        self.resourcesCost = InfeasConstr.calcResourcesCost(self.diff, self.resourceType)
        self.priority = 0
        
    def incrementPriority(self):
        self.priority = self.priority + 1 
    @staticmethod
    def calcResourcesCost(diff, resourceType):
        cost = 0
        if resourceType == "cpu":
            cost = diff
        elif resourceType == "mem":
            cost = diff / 1000
        elif resourceType == "dsk":
            cost = diff / 100
        return cost

    #Calculate LHS of a constraint
    @staticmethod
    def calcLHS(model, c):
        LHS = 0
        row = model.getRow(model.getConstrByName(c))
        for k in range(row.size()):
            LHS += row.getCoeff(k)
        return LHS

    @staticmethod
    def findConstrServerName(constraintName):
        serverName =""
        if "c4(n" in constraintName:
            pattern = "\((.*?)\)"
            serverName = re.search(pattern, constraintName).group(1)
        return serverName

    @staticmethod              
    def findConstrResourceType(constraintName):
        resourceType =""
        if "cpu" in constraintName:
            resourceType = "cpu"
        elif "mem" in constraintName:
            resourceType = "mem"
        elif "dsk" in constraintName:
            resourceType = "dsk"
        return resourceType