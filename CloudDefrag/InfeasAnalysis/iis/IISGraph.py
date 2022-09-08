from itertools import chain, combinations

def powerset(iterable):
    #Get all subsets of a set
    #Ref: https://stackoverflow.com/questions/1482308/how-to-get-all-subsets-of-a-set-powerset
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

def blockUp(constraintsPowerSet, IIS):
    originalConstraintsPowerSet = constraintsPowerSet.copy()
    for s in reversed(originalConstraintsPowerSet):
            if set(IIS).issubset(set(s)):
                constraintsPowerSet.remove(s)

def blockDown(constraintsPowerSet, seed):
    originalConstraintsPowerSet = constraintsPowerSet.copy()
    for s in reversed(originalConstraintsPowerSet):
            if set(s).issubset(set(seed)):
                constraintsPowerSet.remove(s)

def shrink(subModel, constraintsPowerSet, constraints, constraintsDictionary, IISes):
    
    seed = set(constraintsPowerSet[-1])                                 #Get the seed
    constraintsToBeRemoved = set(constraints).difference(set(seed))
    #Remove all constraints not in the seed from the model
    for i in constraintsToBeRemoved:
        subModel.remove(subModel.getConstrs()[i])
    subModel.update()
    #Important note: indeces changed in subModel after remove! Therefore, we need the dictionary
    IIS = []
    
    #Current optimization status for the model. Status values are described in the Status Code section.
    # https://www.gurobi.com/documentation/9.5/refman/optimization_status_codes.html#sec:StatusCodes
    # print(model.Status)

    subModel.optimize()
    
    #Get Seed model Status
    status = subModel.Status
    #https://www.gurobi.com/documentation/9.5/refman/dualreductions.html#parameter:DualReductions
    if status == 4:
        subModel.Params.DualReductions = 0
        subModel.optimize()
        status = subModel.Status
    
    if status == 2 or status == 5:
        IIS = []
        blockDown(constraintsPowerSet, seed)
        

    elif status == 3:
        subModel.computeIIS()
        for c in subModel.getConstrs():
            isPartOfSelectedConstrs = c.index in constraints
            if c.IISConstr and isPartOfSelectedConstrs:
                IIS.append(constraintsDictionary[c.ConstrName])

        isIISDublicate = False
        for i in IISes:
            if set(i) == set(IIS):
                isIISDublicate = True
                break
        if isIISDublicate:
            IIS = []
            constraintsPowerSet.remove(constraintsPowerSet[-1])    
        else:
            blockUp(constraintsPowerSet, IIS)
        
    return set(IIS)
