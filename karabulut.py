# This work is licensed under CC BY-NC 4.0 
# Authors: Cornejo-Acosta, J.A.; Garcia-Diaz, J.; Perez-Sansalvador, J.C.; Segura, C. 

import math
import os
import sys
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
    not_routed = set(range(n))
    track = []
    for i in range(n):
        track.append([])

    for e in edges:
        track[e[0]].append(e[1])
        track[e[1]].append(e[0])

    tours = []
    while len(not_routed) > 0:
        v = not_routed.pop()
        tour = [v, track[v][0]]
        not_routed.remove(track[v][0])

        while tour[-1] != tour[0]:
            # there are two possible elements per track[i]
            if track[tour[-1]][0] != tour[-2]:
                v = track[tour[-1]][0]
            else:
                v = track[tour[-1]][1]

            tour.append(v)
            if tour[0] != v:
                not_routed.remove(v)

        # remove repeated vertex from tour
        tour.pop()
        tours.append(tour)

    return tours


def solve(file_instance: str, m: int, U: int, BestObjStop=None, MemLimit=0.01, TimeLimit=5, objective="minsum", presolve=2, MIPGap=0.0,
          outputFlag=0):
    try:
        global t_inc, objval
        t_inc = math.inf
        objval = math.inf

        D, I = read_TSPLIB_instance(file_instance)
        n = len(D)
        if U > n:
            U = n
        inputparams["U"] = U

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
                x.append([0] * m)

        for i in range(n):
            for j in range(n):
                xk = []
                for k in range(m):
                    xk.append(model.addVar(vtype=GRB.BINARY,
                              name="x{}{}{}".format(i, j, k)))
                x[i][j] = xk

        t = []
        z = []
        for i in range(n):
            t.append(model.addVar(vtype=GRB.CONTINUOUS, name='t{}'.format(i)))
            z.append(model.addVar(vtype=GRB.BINARY, name='z{}'.format(i)))

        # constraints

        # (14)
        for j in range(n):
            cs14 = 0
            for i in range(n):
                if i != j:
                    cs14 += quicksum(x[i][j][k] for k in range(m))
            model.addConstr(cs14 == 1)

        # (15)
        for p in range(n):
            for k in range(m):
                model.addConstr(quicksum(x[i][p][k] for i in range(n) if i != p) -
                                quicksum(x[p][j][k] for j in range(n) if j != p) == 0)

        # (16)
        for k in range(m):
            cs16 = 0
            for i in range(n):
                cs16 += quicksum(x[i][j][k] for j in range(n) if i != j)
            model.addConstr(cs16 >= 1)

        # (17)
        for i in range(n):
            for j in range(n):
                if i != j:
                    model.addConstr(t[i] - t[j] + U * quicksum(x[i][j][k]
                                    for k in range(m)) <= U - 1 + U * z[j])

        # (18)
        for i in range(n):
            model.addConstr(1 <= t[i])
            model.addConstr(t[i] <= U)

        # (19)
        model.addConstr(quicksum(z) == m)

        if objective == "minsum":
            minsum = 0
            for i in range(n):
                for j in range(n):
                    if i != j:
                        minsum += D[i][j] * \
                            quicksum(x[i][j][k] for k in range(m))

            # minsum objective function
            model.setObjective(minsum)

        elif objective == "minmax":
            Smax = model.addVar(vtype=GRB.INTEGER, name="Smax")
            # (22)
            for k in range(m):
                cs22 = 0
                for i in range(n):
                    cs22 += quicksum(D[i][j] * x[i][j][k]
                                     for j in range(n) if i != j)
                model.addConstr(Smax >= cs22)

            # minmax objective function
            model.setObjective(Smax)

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
        edges = []
        for i in range(n):
            for j in range(n):
                for k in range(m):
                    if x[i][j][k].X > 0.9:
                        edges.append((i, j))
                        # print(str(i) + ', ' + str(j))

        tours = build_path(edges, n)
    else:
        tours = []

    return tours, fitness, runtime, gap, t_inc


def run_karabulut(conf):
    global inputparams
    inputparams = {"IP": conf["IP"]}  # register of input parameters

    output_file = conf["outputFile"]
    inputparams["outputFile"] = output_file
    if os.path.exists(output_file):
        os.remove(output_file)

    file_instance = conf["instance"]
    inputparams["instance"] = file_instance

    m = conf["m"]
    inputparams["m"] = m

    L = conf["L"]
    if L != 2:
        L = 2
    inputparams["L"] = L

    U = conf["U"]
    inputparams["U"] = U

    objective = conf["objective"]
    inputparams["objective"] = objective

    variant = conf["variant"]
    if variant != "CP":
        variant = "CP"
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

    tours, fitness, runtime, gap, t_inc = solve(file_instance=file_instance, m=m, U=U, BestObjStop=BestObjStop, MemLimit=MemLimit,
                                                TimeLimit=TimeLimit, objective=objective,
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
