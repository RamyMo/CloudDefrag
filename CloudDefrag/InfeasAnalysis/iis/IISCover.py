import re

class IISCover:
    def __init__(self, model, constraints) -> None:
        self.model = model
        self.constraints = constraints
        self.numOfConstraints = len(constraints)
        self.addedCPU = IISCover.calcAddedCPU(model, constraints)
        self.addedMem = IISCover.calcAddedMem(model, constraints)
        self.addedDisk = IISCover.calcAddedDisk(model, constraints)
        self.serversUsed = IISCover.findServersUsedNames(constraints)
        self.numOfServersUsed = len(self.serversUsed)
        self.resourcesCostEst = self.addedCPU + (self.addedDisk / 100) + (self.addedMem / 1000)

    #Calculate LHS of a constraint
    @staticmethod
    def calcLHS(model, c):
        LHS = 0
        row = model.getRow(model.getConstrByName(c))
        for k in range(row.size()):
            LHS += row.getCoeff(k)
        return LHS

    @staticmethod
    def calcAddedCPU(model, constraints):
        cpu = 0
        for c in constraints:
            if "cpu" in c:
                RHS = model.getConstrByName(c).RHS
                LHS = IISCover.calcLHS(model, c)
                diff = abs(RHS - LHS)
                cpu += diff
        return cpu

    @staticmethod    
    def calcAddedMem(model, constraints):
        mem = 0
        for c in constraints:
            if "mem" in c:
                RHS = model.getConstrByName(c).RHS
                LHS = IISCover.calcLHS(model, c)
                diff = abs(RHS - LHS)
                mem += diff
        return mem

    @staticmethod
    def calcAddedDisk(model, constraints):
        disk = 0
        for c in constraints:
            if "dsk" in c:
                RHS = model.getConstrByName(c).RHS
                LHS = IISCover.calcLHS(model, c)
                diff = abs(RHS - LHS)
                disk += diff
        return disk

    @staticmethod
    def findServersUsedNames(constraints):
        serversNames = [] 
        for c in constraints:
            if "c4(n" in c:
                pattern = "\((.*?)\)"
                serverName = re.search(pattern, c).group(1)
                # print(serverName)
                if serverName not in serversNames:
                    serversNames.append(serverName)

        return serversNames

