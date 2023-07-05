# This work is licensed under CC BY-NC 4.0 
# Authors: Cornejo-Acosta, J.A.; Garcia-Diaz, J.; Perez-Sansalvador, J.C.; Segura, C. 

import math
import os
from pathlib import Path

import gurobipy as gp
from gurobipy import GRB, quicksum

from TSPLIBReader import read_TSPLIB_instance

convergence = []
def callback_incumbent_logger(model, where):
    if where == GRB.Callback.MIPSOL:

        this_objval = model.cbGet(GRB.Callback.MIPSOL_OBJ)
        this_time = model.cbGet(GRB.Callback.RUNTIME)

        global t_inc, objval
        if objval != this_objval:
            objval = this_objval
            t_inc = this_time
            convergence.append([this_time, this_objval])


def build_path(edges: list, n: int):
    endpoints = set(range(n))
    track = []
    for i in range(n):
        track.append([])
    
    for e in edges:
        track[e[0]].append(e[1])
        if len(track[e[0]]) == 2:
            endpoints.remove(e[0])
        
        track[e[1]].append(e[0])
        if len(track[e[1]]) == 2:
            endpoints.remove(e[1])
    
    tours = []
    while len(endpoints) > 0:
        v = endpoints.pop()
        tour = [v, track[v][0]]
        while len(track[tour[-1]]) == 2:
            # there are two possible elements per track[i]
            if track[tour[-1]][0] != tour[-2]:
                v = track[tour[-1]][0]
            else:
                v = track[tour[-1]][1]
            tour.append(v)
        
        # remove the last vertex of tour from endpoints
        endpoints.remove(tour[-1])
        tours.append(tour)
    
    return tours


def solve(file_instance: str, m: int, L: int, U: int, R=[], IQP=True, BestObjStop=None, MemLimit=0.01, TimeLimit=5, objective="minsum",
          variant="CP", presolve=2, MIPGap=0.0, outputFlag=0):
    try:
        global t_inc, objval
        t_inc = math.inf
        objval = math.inf
        
        C, I = read_TSPLIB_instance(file_instance)
        n = len(C) + m
        if U > n-m:
            U = n-m
            inputparams["U"] = U

        if L > U:
            L = 2
            inputparams["L"] = L
        
        # add dummy depots
        for i in range(m):
            C.insert(0, [0] * n)
        for i in range(m, n):
            for j in range(m):
                C[i].insert(0, 0)
        
        env = gp.Env(empty=True)
        env.setParam("MemLimit", MemLimit)
        env.start()
        
        model = gp.Model(env=env)
        model.setParam("presolve", presolve)
        model.Params.outputFlag = outputFlag
        model.setParam("MIPGap", MIPGap)
        model.setParam("TimeLimit", TimeLimit)

        if BestObjStop is not None:
            model.setParam("BestObjStop", BestObjStop)
        
        # add variables
        x = []
        for i in range(n):
            x.append([0] * n)
        
        for i in range(n):
            for j in range(n):
                xk = []
                for k in range(m):
                    xk.append(model.addVar(vtype=GRB.BINARY,
                                           name="x{},{},{}".format(i, j, k)))
                x[i][j] = xk
        
        t = []
        for i in range(n):
            t.append(model.addVar(vtype=GRB.CONTINUOUS,
                                  name='t{}'.format(i)))
        
        # constraints
        D = []  # dummy depots set
        V = []  # actual vertices in G=(V, E)
        for i in range(n):
            if i < m:
                D.append(i)
            else:
                V.append(i)
        
        # (2)
        for k in D:
            model.addConstr(quicksum(x[k][j][k] for j in V) == 1)
        
        # (3)
        for j in V:
            model.addConstr(
                quicksum(x[k][j][k] for k in D) +
                quicksum(quicksum(x[i][j][k] for i in V) for k in D) == 1)
        
        # (4)
        for j in V:
            for k in D:
                model.addConstr(
                    x[k][j][k] + quicksum(x[i][j][k] for i in V) -
                    x[j][k][k] - quicksum(x[j][i][k] for i in V) == 0)
        
        # (5)
        for k in D:
            model.addConstr(quicksum(x[k][j][k] for j in V) - quicksum(x[j][k][k] for j in V) == 0)
        
        # (6); (7); (8)
        for i in V:
            # (6)
            model.addConstr(t[i] + (U - 2) * quicksum(x[k][i][k] for k in D) - quicksum(x[i][k][k] for k in D) <= U - 1)
            
            # (7)
            model.addConstr(t[i] + quicksum(x[k][i][k] for k in D) + (2 - L) * quicksum(x[i][k][k] for k in D) >= 2)
            
            # (8)
            model.addConstr(quicksum(x[k][i][k] for k in D) + quicksum(x[i][k][k] for k in D) <= 1)
        
        # (9)
        for i in V:
            for j in V:
                model.addConstr(t[i] - t[j] + U * quicksum(x[i][j][k] for k in D) +
                                (U - 2) * quicksum(x[j][i][k] for k in D) <= U - 1)
        
        if variant == "CP" and IQP is False:
            # add y variables
            y = []
            for i in range(n):
                y.append([0] * n)
            
            for i in range(n):
                for j in range(n):
                    yk = []
                    for k in range(m):
                        yk.append(model.addVar(vtype=GRB.BINARY, name="y{},{},{}".format(i, j, k)))
                    y[i][j] = yk
            
            # new constraints for y variables
            for k in D:
                for j in V:
                    for i in V:
                        model.addConstr(y[i][j][k] >= x[i][k][k] + x[k][j][k] - 1)  # (16)
                        model.addConstr(y[i][j][k] <= x[k][j][k])  # (17)
                        model.addConstr(y[i][j][k] <= x[i][k][k])  # (18)
                        
                        # for FD-M+DL
        if R is not None:
            R = [x + m for x in R]
            
            # (26)
            model.addConstr(quicksum(quicksum(x[k][i][k] for i in R) for k in D) == len(R))
        
        if objective == "minsum":
            
            # quadratic objective function
            if variant == "CP" and IQP is True:
                # (1)
                model.setObjective(
                    quicksum(
                        quicksum(
                            C[i][j] * quicksum(x[i][j][k] + x[i][k][k] * x[k][j][k] for k in D)
                            for j in V)
                        for i in V)
                )
            
            # linear objective function
            elif variant == "CP" and IQP is False:
                # (15)
                model.setObjective(
                    quicksum(
                        quicksum(
                            C[i][j] * quicksum(x[i][j][k] + y[i][j][k] for k in D)
                            for j in V)
                        for i in V)
                )
            
            elif variant == "OP":
                # (23)
                model.setObjective(
                    quicksum(
                        quicksum(
                            C[i][j] * quicksum(x[i][j][k] for k in D)
                            for j in V)
                        for i in V)
                )
        
        elif objective == "minmax":
            Pmax = model.addVar(vtype=GRB.INTEGER, name="Pmax")
            model.setObjective(Pmax)
            
            # quadratic objective function
            if variant == "CP" and IQP is True:
                # (21)
                for k in range(m):
                    model.addConstr(Pmax >=
                                    quicksum(
                                        quicksum(C[i][j] * (x[i][j][k] + x[i][k][k] * x[k][j][k]) for j in V)
                                        for i in V))
            
            # linear objective function
            elif variant == "CP" and IQP is False:
                for k in range(m):
                    model.addConstr(Pmax >=
                                    quicksum(
                                        quicksum(C[i][j] * (x[i][j][k] + y[i][j][k]) for j in V)
                                        for i in V))
            
            elif variant == "OP":
                # (25)
                for k in range(m):
                    model.addConstr(Pmax >=
                                    quicksum(
                                        quicksum(C[i][j] * x[i][j][k] for j in V)
                                        for i in V))
        
        else:
            raise ValueError("Invalid objective function!")
        
        # attach callback for get incumbent time
        model.optimize(callback_incumbent_logger)
    
    except gp.GurobiError as e:
        if e.errno != 10001:
            print('Error code ' + str() + ': ' + str(e))
            raise RuntimeError("Error at solving procedure!")
    
    runtime = model.Runtime
    fitness = model.objVal
    gap = model.MIPGap
    
    if model.SolCount > 0:
        # remove dummy depots
        # for FD-M+DL
        if R is not None:
            R = [x - m for x in R]
        n = n - m
        for i in range(m):
            del C[0]
            del x[0]
        for i in range(n):
            for j in range(m):
                del C[i][0]
                del x[i][0]
        
        edges = []
        for i in range(n):
            for j in range(n):
                for k in range(m):
                    if x[i][j][k].X > 0.9:
                        edges.append((i, j))
        
        tours = build_path(edges, n)
    
    else:
        tours = []
    
    return tours, fitness, runtime, gap, t_inc


def run_IP1(conf):

    global inputparams
    inputparams = {"IP":conf["IP"]} # register of input parameters

    output_file = conf["outputFile"]
    inputparams["outputFile"] = output_file
    if os.path.exists(output_file):
        os.remove(output_file)

    file_instance = conf["instance"]
    inputparams["instance"] = file_instance

    m = conf["m"]
    inputparams["m"] = m

    L = conf["L"]
    if L < 2:
        L = 2
    inputparams["L"] = L

    U = conf["U"]
    inputparams["U"] = U

    IQP = conf["IQP"]
    inputparams["IQP"] = IQP

    R = conf["R"]
    inputparams["R"] = R

    objective = conf["objective"]
    inputparams["objective"] = objective

    variant = conf["variant"]
    inputparams["variant"] = variant

    BestObjStop = None
    if "BestObjStop" in conf:
        BestObjStop = conf["BestObjStop"]
        inputparams["BestObjStop"] = BestObjStop

    MemLimit = conf["MemLimit"]
    inputparams["MemLimit"] = MemLimit

    TimeLimit = conf["TimeLimit"]
    inputparams["TimeLimit"] = TimeLimit

    presolve = conf["presolve"]
    inputparams["presolve"] = presolve

    MIPGap = conf["MIPGap"]
    inputparams["MIPGap"] = MIPGap

    outputFlag = conf["outputFlag"]
    inputparams["outputFlag"] = outputFlag
    
    tours, fitness, runtime, gap, t_inc = solve(file_instance=file_instance, m=m, L=L, U=U, R=R, IQP=IQP,
                                                BestObjStop=BestObjStop, MemLimit=MemLimit,
                                                TimeLimit=TimeLimit, objective=objective, variant=variant,
                                                presolve=presolve, MIPGap=MIPGap, outputFlag=outputFlag)
    
    with open(output_file, "a") as writer:
        ignored = conf.copy()

        output_dict = {}
        # input configuration
        INPUT_dict = {}
        INPUT_default = []
        for key, value in inputparams.items():
            INPUT_dict[key] = value
            if ignored[key] != value:
                INPUT_default.append(key)
            else:
                del ignored[key]

        if len(INPUT_default)>0:
            INPUT_dict["default"] = INPUT_default
        output_dict["INPUT"] = INPUT_dict

        # print ignored parameters
        if len(ignored)>0:
            output_dict["IGNORED_PARAMETERS"] = ignored

        OUTPUT_dict = {}
        # output
        OUTPUT_dict["objval"] = str(fitness)
        OUTPUT_dict["runtime"] = runtime
        OUTPUT_dict["gap"] = str(gap)
        OUTPUT_dict["timeinc"] = str(t_inc)
        OUTPUT_dict["paths"] = tours
        OUTPUT_dict["convergence"] = convergence

        output_dict["OUTPUT"] = OUTPUT_dict

        import json
        writer.write(json.dumps(output_dict))

    print("output printed in {}".format(output_file))
    