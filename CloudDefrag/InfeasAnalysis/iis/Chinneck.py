from pickle import FALSE, TRUE
import gurobipy as gp
from gurobipy import *
from gurobipy.gurobipy import Model
from CloudDefrag.InfeasAnalysis.iis.ModelLib import AdvancedModel
from CloudDefrag.InfeasAnalysis.iis import IISCompute
import  multiprocessing
from CloudDefrag.InfeasAnalysis.iis.IISCompute import InfeasConstr
from CloudDefrag.InfeasAnalysis.iis.IISCover import IISCover

class IISFinder:
    #Constructor
    def __init__(self, model) -> None:
        self.model = model
        self.method = "DeletionFilter"

    #Setters
    def setModel(self, model):
        self.model = model

    def setMethod(self, method):
        self.method = method

    #Getters
    def getModel(self):
        return self.model

    def getMethod(self):
        return self.method

    #Methods
    def findIIS(self):
        if self.method =="DeletionFilter":
            return self.__deletionFilter()
        elif self.method =="AddDeleteFilter":
            return self.__addDeleteFilter()
        elif self.method =="GRB":
            return self.__gurobiComputeIIS()

    def __deletionFilter(self):
        model = self.model
        advModel = AdvancedModel(model)
        IIS = []
        for c in model.getConstrs():
            if "c4(n" in c.ConstrName: 
                reducedModel = advModel.dropConstraint(c.ConstrName)
                if IISCompute.isFeasible(reducedModel):
                    IIS.append(c.ConstrName)    
                else:
                    advModel = AdvancedModel(reducedModel)
        return IIS
   
    def __deletionFilterOrg(self):
        model = self.model
        advModel = AdvancedModel(model)
        IIS = []
        for c in model.getConstrs():
            reducedModel = advModel.dropConstraint(c.ConstrName)
            if IISCompute.isFeasible(reducedModel):
                if "c4(n" in c.ConstrName:                        #Enable only if you want to include modifiable constrs only
                    IIS.append(c.ConstrName)    
            else:
                advModel = AdvancedModel(reducedModel)
        return IIS
   
    def __addDeleteFilter(self):
        advModel = AdvancedModel(self.model)
        IIS = []
        T = advModel.dropModifiableConstraints()
        for c in self.model.getConstrs():
            if "c4(n" in c.ConstrName: 
                advModel.addConstraint(T, c.ConstrName)
                if not IISCompute.isFeasible(T):
                    break

        model = T
        advModel = AdvancedModel(model)
        IIS = []
        for c in model.getConstrs():
            if "c4(n" in c.ConstrName: 
                reducedModel = advModel.dropConstraint(c.ConstrName)
                if IISCompute.isFeasible(reducedModel):
                    IIS.append(c.ConstrName)    
                else:
                    advModel = AdvancedModel(reducedModel)
        return IIS

    def __gurobiComputeIIS(self):
        advModel = AdvancedModel(self.model)
        model = advModel.copyModel()
        IIS = IISCompute.computeIIS(model)
        return IIS

class IISesFinder:
    #Constructor
    def __init__(self, model) -> None:
        self.model = model
        self.advancedModel = AdvancedModel(model)
        self.method = "DeletionFilter"
        self.IISes = []
        self.maxShuffles = 1
        self.maxNumOfProcesses = 1

    #Setters
    def setModel(self, model):
        self.model = model

    def setMethod(self, method):
        self.method = method
    
    def setAdvancedModel(self, advancedModel):
        self.advancedModel = advancedModel

    def setMaxShuffles(self, maxShuffles):
        self.maxShuffles = maxShuffles
    
    def setMaxNumOfProcesses(self, maxNumOfProcesses):
        self.maxNumOfProcesses = maxNumOfProcesses

    #Getters
    def getModel(self):
        return self.model

    def getMethod(self):
        return self.method
    
    def getAdvancedModel(self):
        return self.advancedModel
    
    def getMaxShuffles(self):
        return self.maxShuffles
   
    def getIISes(self):
       return self.IISes

    def getMaxNumOfProcesses(self):
        return self.maxNumOfProcesses
    #Methods
    def findIISes(self):
        advModel = self.advancedModel
        for i in range(self.maxShuffles):
            shuffledModel = advModel.shuffleModel()
            iisFinder = IISFinder(shuffledModel) 
            IIS = iisFinder.findIIS()
            isIISunique = True
            for i in self.IISes:
                if set(i) == set(IIS):
                    isIISunique = False
                    break
            if isIISunique:
                self.IISes.append(IIS)
        return self.IISes
    
    def findIISesParallel(self):
        manager = multiprocessing.Manager()
        return_dict = manager.dict()
        maxNumOfProcesses = self.maxNumOfProcesses
        self.IISes = []
        p = []
        for i in range(maxNumOfProcesses) :
            p.append(Process(i, self, return_dict))
            p[i].start()
        for i in range(maxNumOfProcesses) :
            p[i].join()    
        for i in range(maxNumOfProcesses) :
            currentIISes = return_dict[i]
            for iis in currentIISes:
                isIISunique = True
                for j in self.IISes:
                    if set(j) == set(iis):
                        isIISunique = False
                        break
                if isIISunique:
                    self.IISes.append(iis)
        return self.IISes


    def printIISes(self):
        print("\n\t\t*** IISes Info. ***")
        print("Number of Processes = ", self.getMaxNumOfProcesses())
        print("Number of Shuffles = ", self.getMaxShuffles())
        print("Number of IISes = ", len(self.IISes))
        for i in self.IISes:
            print(i)
    # Process class
class Process(multiprocessing.Process):
    def __init__(self, id, iisesFinder, return_dict):
        super(Process, self).__init__()
        self.id = id
        self.iisesFinder = iisesFinder
        self.return_dict = return_dict
  
    def run(self):
        IISes = self.iisesFinder.findIISes()
        self.return_dict[self.id] = IISes


    
class IISRelaxer:
    #Constructor
    def __init__(self, model, IISes) -> None:
        self.model = model
        self.IISes = IISes
        self.IISesConstraints = []
        self.IISesConstraintsDict = dict()
        self.exploredIISesConstraints = []
        self.advancedModel = AdvancedModel(model)
        self.IISCover = []
    
    #Setters

    #Getters

    #Methods
    def findIISesConstraints(self):
        for iis in self.IISes:
            for c in iis:
                if c not in self.exploredIISesConstraints:
                    self.exploredIISesConstraints.append(c)
                    infConstr = InfeasConstr(self.model, c)
                    infConstr.incrementPriority()
                    self.IISesConstraints.append(infConstr)
                    self.IISesConstraintsDict[c] = infConstr
                else:
                    self.IISesConstraintsDict[c].incrementPriority()
        self.IISesConstraints.sort(key=lambda x: x.priority , reverse=True) 
        return self.IISesConstraints

    def printIISesConstraints(self):
        print("\n\t\t*** Initial IISes Table ***")
        print("Name\t\t Priority \tCost")
        for c in self.IISesConstraints:
            print(c.constraintName,"\t", c.priority,"\t\t", c.resourcesCost)

    def printIISes(self):
        print("Number of IISes = ", len(self.IISes))
        for i in self.IISes:
            print(i)
    
    def addIIS(self, IIS):
        isIISunique = True
        for i in self.IISes:
            if set(i) == set(IIS):
                isIISunique = False
                return
        if isIISunique:
            self.IISes.append(IIS)
            for c in IIS:
                if c not in self.exploredIISesConstraints:
                    self.exploredIISesConstraints.append(c)
                    infConstr = InfeasConstr(self.model, c)
                    infConstr.incrementPriority()
                    self.IISesConstraints.append(infConstr)
                    self.IISesConstraintsDict[c] = infConstr
                else:
                    self.IISesConstraintsDict[c].incrementPriority()
            self.IISesConstraints.sort(key=lambda x: x.priority , reverse=True) 

    def relaxToFeasbilityGurobi(self):
        model = self.advancedModel.copyModel()
        modifiableConstraints = []                          #List of modif. constrs names
        IISCompute.findModifConstrs(model, modifiableConstraints)
        if IISCompute.isFeasible(model) == True:
            print("Model was proven to be feasible.")
            return []
        iisCover = [] 
        while IISCompute.isFeasible(model) == False: 
            IIS = IISCompute.computeIIS(model)                          #Compute IIS using Gurobi Method
            IISCompute.reduceIIS(IIS, modifiableConstraints)                 #Remove unmodifiable constraints
            self.addIIS(IIS)
            #Relax constraints from the same group of the last constraint relaxed first
            continueToNext = False
            if iisCover:
                lastServerUsedName = InfeasConstr.findConstrServerName(iisCover[-1]) 
                for c in IIS:
                    if lastServerUsedName in c:
                        relaxedConstraint = c
                        iisCover.append(relaxedConstraint)
                        model.remove(model.getConstrByName(relaxedConstraint)) 
                        model.update()
                        continueToNext = True
                        break

            if continueToNext:
                continue

            currentIISesConstraints = []
            for c in IIS:
                currentIISesConstraints.append(self.IISesConstraintsDict[c])
            currentIISesConstraints.sort(key=lambda x: x.priority , reverse=True)
            highestPriority = currentIISesConstraints[0].priority
            currentIISesConstraintsHighestPrio =[]
            for c in currentIISesConstraints:
                if c.priority == highestPriority:
                    currentIISesConstraintsHighestPrio.append(c)
            currentIISesConstraintsHighestPrio.sort(key=lambda x: x.resourcesCost , reverse=False)

            # self.printIISes()
            # self.printIISesConstraints()

            # print("currentIISesConstraints")
            # for c in currentIISesConstraints:
            #     print("Name: ", c.constraintName, " Priority: ",c.priority, " Cost: ", c.resourcesCost)
            
            # print("Select: ", currentIISesConstraintsHighestPrio[0].constraintName)
            relaxedConstraint = currentIISesConstraintsHighestPrio[0].constraintName
            if relaxedConstraint not in iisCover:
                iisCover.append(relaxedConstraint)
                model.remove(model.getConstrByName(relaxedConstraint)) 
                model.update()
       
        self.IISCover = IISCover(self.model, iisCover)

        return self.IISCover

    def relaxToFeasbilityLoop(self):
        model = self.advancedModel.copyModel()
        # modifiableConstraints = []                          #List of modif. constrs names
        # IISCompute.findModifConstrs(model, modifiableConstraints)
        if IISCompute.isFeasible(model) == True:
            print("Model was proven to be feasible.")
            return []
        iisCover = [] 
        isFirstIteration = True
        while IISCompute.isFeasible(model) == False: 
            if not isFirstIteration:
                iisesFinder = IISesFinder(model)
                iisesFinder.setMaxShuffles(8)
                iisesFinder.setMaxNumOfProcesses(8)
                IISes = iisesFinder.findIISesParallel() 
                for IIS in IISes:
                    self.addIIS(IIS)
            else:
                IISes = self.IISes
            
            # print("IISes: ")
            # for i in self.IISes:
            #     print(i)

            isFirstIteration = False
            # self.printIISesConstraints()
            #Relax constraints from the same group of the last constraint relaxed first
            continueToNext = False
            currentExploredIISesConstraints = []
            for iis in IISes:
                for c in iis:
                    if c not in currentExploredIISesConstraints:
                        currentExploredIISesConstraints.append(c)

            if iisCover:
                lastServerUsedName = InfeasConstr.findConstrServerName(iisCover[-1]) 
                for c in currentExploredIISesConstraints:
                    if lastServerUsedName in c:
                        relaxedConstraint = c
                        iisCover.append(relaxedConstraint)
                        # print("Relax: ", relaxedConstraint)
                        model.remove(model.getConstrByName(relaxedConstraint)) 
                        model.update()
                        continueToNext = True
                        break

            if continueToNext:
                continue
            
            currentIISesConstraints = []
            for IIS in IISes:
                for c in IIS:
                    currentIISesConstraints.append(self.IISesConstraintsDict[c])
            currentIISesConstraints.sort(key=lambda x: x.priority , reverse=True)
            highestPriority = currentIISesConstraints[0].priority
            currentIISesConstraintsHighestPrio =[]
            for c in currentIISesConstraints:
                if c.priority == highestPriority:
                    currentIISesConstraintsHighestPrio.append(c)
            currentIISesConstraintsHighestPrio.sort(key=lambda x: x.resourcesCost , reverse=False)

            relaxedConstraint = currentIISesConstraintsHighestPrio[0].constraintName
            # print("Relax: ", relaxedConstraint)
            if relaxedConstraint not in iisCover:
                iisCover.append(relaxedConstraint)
                model.remove(model.getConstrByName(relaxedConstraint)) 
                model.update()
       
        self.IISCover = IISCover(self.model, iisCover)

        return self.IISCover
  
    def relaxToFeasbilityLoopCover(self):
        model = self.advancedModel.copyModel()
        # modifiableConstraints = []                          #List of modif. constrs names
        # IISCompute.findModifConstrs(model, modifiableConstraints)
        if IISCompute.isFeasible(model) == True:
            print("Model was proven to be feasible.")
            return []
        iisCover = [] 
        isFirstIteration = True
        while IISCompute.isFeasible(model) == False: 
            if not isFirstIteration:
                iisesFinder = IISesFinder(model)
                iisesFinder.setMaxShuffles(8)
                iisesFinder.setMaxNumOfProcesses(8)
                IISes = iisesFinder.findIISesParallel() 
                for IIS in IISes:
                    self.addIIS(IIS)
            else:
                IISes = self.IISes
            
            # print("IISes: ")
            # for i in self.IISes:
            #     print(i)

            isFirstIteration = False
            # self.printIISesConstraints()
            #Relax constraints from the same group of the last constraint relaxed first
            continueToNext = False
            currentExploredIISesConstraints = []
            for iis in IISes:
                for c in iis:
                    if c not in currentExploredIISesConstraints:
                        currentExploredIISesConstraints.append(c)

            if iisCover:
                lastServerUsedName = InfeasConstr.findConstrServerName(iisCover[-1]) 
                for c in currentExploredIISesConstraints:
                    if lastServerUsedName in c:
                        relaxedConstraint = c
                        iisCover.append(relaxedConstraint)
                        # print("Relax: ", relaxedConstraint)
                        model.remove(model.getConstrByName(relaxedConstraint)) 
                        model.update()
                        continueToNext = True
                        break

            if continueToNext:
                continue
        
            
            while IISes:
                currentIISesConstraints = []
                for IIS in IISes:
                    for c in IIS:
                        currentIISesConstraints.append(self.IISesConstraintsDict[c])
                currentIISesConstraints.sort(key=lambda x: x.priority , reverse=True) 
                highestPriority = currentIISesConstraints[0].priority
                currentIISesConstraintsHighestPrio =[]            
                for c in currentIISesConstraints:
                    if c.priority == highestPriority:
                        currentIISesConstraintsHighestPrio.append(c)
                currentIISesConstraintsHighestPrio.sort(key=lambda x: x.resourcesCost , reverse=False)
                relaxedConstraint = currentIISesConstraintsHighestPrio[0].constraintName
                IISesComplete = IISes.copy()
                for IIS in IISesComplete:
                    if relaxedConstraint in IIS:
                        IISes.remove(IIS)
                # print("Relax: ", relaxedConstraint)
                if relaxedConstraint not in iisCover:
                    iisCover.append(relaxedConstraint)
                    model.remove(model.getConstrByName(relaxedConstraint)) 
                    model.update()
       
        self.IISCover = IISCover(self.model, iisCover)

        return self.IISCover
