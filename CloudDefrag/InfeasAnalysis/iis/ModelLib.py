import random
import gurobipy as gp
from gurobipy import *
from gurobipy.gurobipy import Model


class AdvancedModel:
    #Constructor
    def __init__(self, model) -> None:
        self.model = model
        
    
    #Setters
    def setModel(self, model):
        self.model = model

    #Getters
    def getModel(self):
        return self.model

    #Return a new copy of the model
    def copyModel(self):
        model = self.model
        copiedModel = Model("copied_VNF_Placement")
        newVarsDict = {}
         #Copy Variables
        for v in model.getVars():
            copiedModel.addVar(lb=v.LB, ub=v.UB, obj=v.Obj, vtype=v.VType, name=v.VarName)
            copiedModel.update()
            newV = copiedModel.getVarByName(v.VarName)
            newVarsDict[newV.VarName] = newV                                                        #Save variables to a dictionary based on their names
        #Copy Constraints
        for c in model.getConstrs():
            expr = model.getRow(c)
            newexpr = LinExpr()
            for i in range(expr.size()):
                v = expr.getVar(i)
                coeff = expr.getCoeff(i)
                newv = newVarsDict[v.Varname]
                newexpr.add(newv, coeff)
            copiedModel.addLConstr(newexpr, c.Sense, c.RHS, name=c.ConstrName)
            copiedModel.update()
        # copiedModel.write('./output/copied_model.lp')
        return copiedModel

    #Return a new shuffled constraints copy of the model
    def shuffleModel(self):
        model = self.model
        # model = gp.read('./ExampleProblems/Gleeson-lp.lp')
        copiedModel = Model("copied_VNF_Placement")
        newVarsDict = {}
         #Copy Variables
        for v in model.getVars():
            copiedModel.addVar(lb=v.LB, ub=v.UB, obj=v.Obj, vtype=v.VType, name=v.VarName)
            copiedModel.update()
            newV = copiedModel.getVarByName(v.VarName)
            newVarsDict[newV.VarName] = newV                                                        #Save variables to a dictionary based on their names
        #Copy and Shuffle Constraints
        shuffled_constrs = model.getConstrs()
        random.shuffle(shuffled_constrs)
        for c in shuffled_constrs:
            expr = model.getRow(c)
            newexpr = LinExpr()
            for i in range(expr.size()):
                v = expr.getVar(i)
                coeff = expr.getCoeff(i)
                newv = newVarsDict[v.Varname]
                newexpr.add(newv, coeff)
            copiedModel.addLConstr(newexpr, c.Sense, c.RHS, name=c.ConstrName)
            copiedModel.update()
        # copiedModel.write('./output/copied_model.lp')
        return copiedModel

    #Return a new copy of the model after dropping the given constraint
    def dropConstraint(self, constraint):
        model = self.model
        copiedModel = Model("copied_VNF_Placement")
        newVarsDict = {}
         #Copy Variables
        for v in model.getVars():
            copiedModel.addVar(lb=v.LB, ub=v.UB, obj=v.Obj, vtype=v.VType, name=v.VarName)
            copiedModel.update()
            newV = copiedModel.getVarByName(v.VarName)
            newVarsDict[newV.VarName] = newV              #Save variables to a dictionary based on their names
        #Copy Constraints
        for c in model.getConstrs():
            if c.ConstrName == constraint:
                continue
            expr = model.getRow(c)
            newexpr = LinExpr()
            for i in range(expr.size()):
                v = expr.getVar(i)
                coeff = expr.getCoeff(i)
                newv = newVarsDict[v.Varname]
                newexpr.add(newv, coeff)
            copiedModel.addLConstr(newexpr, c.Sense, c.RHS, name=c.ConstrName)
            copiedModel.update()
        # copiedModel.write('./output/copied_model.lp')
        return copiedModel

    #Return a new copy of the model after dropping the modifiable constraints (For Additive Filter)
    def dropModifiableConstraints(self):
        model = self.model.copy()
        for c in model.getConstrs():
            if "c4(n" in c.ConstrName:
                model.remove(c) 
        model.update()
        return model

    def dropModifiableConstraintsGroup(self, group_index):
        model = self.model.copy()
        for c in model.getConstrs():
            if group_index in c.ConstrName:
                model.remove(c)
        model.update()
        return model

    def dropModifiableConstraintsGroupbyLocation(self, constraints_group):
        model = self.model.copy()
        for c in model.getConstrs():
            if any(x in c.ConstrName for x in constraints_group):
                model.remove(c)
        model.update()
        return model


        #Return a new copy of the model after adding the given constraint (For Additive Filter)
    def addConstraint(self, sourceModel, constraint):  
        c = self.model.getConstrByName(constraint)
        expr = self.model.getRow(c)
        newexpr = LinExpr()
        for i in range(expr.size()):
            v = expr.getVar(i)
            coeff = expr.getCoeff(i)
            newv =  sourceModel.getVarByName(v.Varname)
            newexpr.add(newv, coeff)
        sourceModel.addLConstr(newexpr, c.Sense, c.RHS, name=c.ConstrName)
        sourceModel.update()
