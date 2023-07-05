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


def build_path(n_prime: int, t: list, D: list):
    single_tour = [0] * n_prime
    for i in range(0, n_prime):
        single_tour[int(t[i].X + 0.5)] = i  # round ti to the nearest integer

    # remove first dummy depot in path
    del single_tour[0]
    del D[0]
    tours = []
    dummy_depot = D[0]
    del D[0]

    tour = []
    for v in single_tour:
        if v != dummy_depot:
            tour.append(v)
        else:
            if len(D) > 0:
                dummy_depot = D[0]
                del D[0]
            tours.append(tour)
            tour = []

    tours.append(tour)
    return tours


def solve(file_instance: str, m: int, L: int, U: int, R=[], IQP=True, BestObjStop=None, MemLimit=0.01, TimeLimit=5, objective="minsum",
          variant="CP", presolve=2, MIPGap=0.0, outputFlag=0):
    try:
        global t_inc, objval
        t_inc = math.inf
        objval = math.inf

        C, I = read_TSPLIB_instance(file_instance)
        n = len(C)
        if U > n:
            U = n
            inputparams["U"] = U

        if L > U:
            L = 2
            inputparams["L"] = L

        # Add m dummy depots
        for i in range(m):
            [x.append(0) for x in C]
        for i in range(m):
            C.append([0] * (n + m))
        n_prime = len(C)

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
        for i in range(n_prime):
            x.append([0] * n_prime)
            for j in range(n_prime):
                x[i][j] = model.addVar(
                    vtype=GRB.BINARY, name="x{},{}".format(i, j))

        t = []
        for i in range(n_prime):
            t.append(model.addVar(vtype=GRB.CONTINUOUS, name="t{}".format(i)))
            if i != n:
                # constraints (33)
                model.addConstr(1 <= t[i])
                model.addConstr(t[i] <= n_prime - 1)
            else:
                # first dummy depot must be the first vertex to be visited
                # constraint (30)
                model.addConstr(t[n] == 0)

        if variant == "CP" and IQP is False:
            y = []
            for i in range(n_prime):
                y.append([0] * n_prime)
                for j in range(n_prime):
                    y[i][j] = model.addVar(
                        vtype=GRB.BINARY, name="y{},{}".format(i, j))

        # FLOW CONSTRAINTS
        # (28)
        for i in range(n_prime):
            model.addConstr(quicksum(x[i][j]
                            for j in range(n_prime) if i != j) == 1)
        # (29)
        for j in range(n_prime):
            model.addConstr(quicksum(x[i][j]
                            for i in range(n_prime) if i != j) == 1)

        # SEC MTZ
        # (34)
        for i in range(n_prime):
            for j in range(n_prime):
                if i != n and j != n:
                    model.addConstr(t[i] - t[j] + x[i][j] *
                                    n_prime <= n_prime - 1)

        # BOUNDING CONSTRAINTS
        if 2 <= L <= U < n:
            for k in range(n, n_prime - 1):
                model.addConstr(t[k + 1] - t[k] <= U + 1)  # (38)
                model.addConstr(t[k + 1] - t[k] >= L + 1)  # (39)

            # last dummy depot
            model.addConstr(n_prime - t[n_prime - 1] <= U + 1)  # (40)
            model.addConstr(n_prime - t[n_prime - 1] >= L + 1)  # (41)

        else:
            # DEPOT ORDERING CONSTRAINTS
            for k in range(n, n_prime - 1):
                model.addConstr(t[k + 1] - t[k] >= 3)  # (31)

            model.addConstr(n_prime - t[n_prime - 1] >= 3)  # (32)

        # # avoid two dummy depots to be connected
        # for i in range(n, n_prime - 1):
        #     model.addConstr(x[i][i+1] == 0)
        # model.addConstr(x[n_prime - 1][n] == 0)

        # # avoid a vertex i to be connected with two dummy depots
        # for i in range(n):
        #     for k in range(n, n_prime-1):
        #         model.addConstr(x[k][i]+x[i][k+1] <= 1)
        #     model.addConstr(x[n_prime - 1][i]+x[i][n] <= 1)

        # EDGES CLOSING PATHS (for linear objective function and closed paths)
        if variant == "CP" and IQP is False:
            for i in range(n):
                for j in range(n):

                    # (45)
                    for k in range(n, n_prime - 1):
                        model.addConstr(y[i][j] >= x[k][j] + x[i][k + 1] - 1)

                    # (46)
                    model.addConstr(y[i][j] >= x[n_prime - 1][j] + x[i][n] - 1)

                    # to avoid possible negative cost edges issues
                    model.addConstr(y[i][j] <= quicksum(x[i][k]
                                    for k in range(n, n_prime)))  # (47)
                    model.addConstr(y[i][j] <= quicksum(x[k][j]
                                    for k in range(n, n_prime)))  # (48)

        if len(R) > 0:
            # FD-M+DL
            for i in R:
                # (51)
                model.addConstr(quicksum(x[k][i]
                                for k in range(n, n_prime)) == 1)

        if objective == "minsum" and (variant == "CP" or variant == "OP"):

            if variant == "CP" and IQP is False:
                # linear objective function
                # (44)
                model.setObjective(
                    quicksum(quicksum(C[i][j] * (x[i][j] + y[i][j])
                             for j in range(n_prime)) for i in range(n_prime))
                )
            elif variant == "CP" and IQP is True:
                # quadratic objective function
                # (27)
                model.setObjective(
                    quicksum(
                        quicksum(
                            C[i][j] * (x[i][j] + x[n_prime - 1][j] * x[i][n] +
                                       quicksum(x[k][j] * x[i][k + 1] for k in range(n, n_prime - 1)))
                            for j in range(n_prime))
                        for i in range(n_prime))
                )
            elif variant == "OP":
                # (50)
                model.setObjective(
                    quicksum(quicksum(C[i][j] * x[i][j]
                             for j in range(n_prime)) for i in range(n_prime))
                )
        else:
            raise ValueError("Invalid objective function or variant!")

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
        tours = build_path(n_prime, t, [d for d in range(n, n_prime)])
    else:
        tours = []
    return tours, fitness, runtime, gap, t_inc


def run_IP2(conf):

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
