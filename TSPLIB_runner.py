# This work is licensed under CC BY-NC 4.0 
# Authors: Cornejo-Acosta, J.A.; Garcia-Diaz, J.; Perez-Sansalvador, J.C.; Segura, C. 

import json
import math
import os
import re


mvals = [3, 5]

instances = ["dantzig42",
             "swiss42",
             "att48",
             "gr48",
             "hk48"
            #  "kroA100",
            #  "kroB100",
            #  "kroC100",
            #  "kroD100",
            #  "kroE100"
             ]

jsoninputname = "tmpinput.json"
output_folder = "may_experiments_tight"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
output_path = "experiments.csv"
with open("{}/{}".format(output_folder, output_path), "a") as writer:
    # IP1IQP			IP1ILP			IP2IQP			IP2ILP
    writer.write("instance,n,m,U,f,t,g,f,t,g,f,t,g,f,t,g\n")

basic_conf = {
    "L": 2,
    "objective": "minsum",
    "variant": "CP",
    "R": [],

    "MemLimit": 12,
    "TimeLimit": 7200,
    "presolve": -1,
    "MIPGap": 0,
    "outputFlag": 1
}
          

def parse_input_file(input_file):
    with open(input_file, 'r') as f:
        data = json.load(f)
        return data


for ins in instances:
    n = int(re.findall(r'\d+', ins)[0])

    for m in mvals:
        U = int(math.ceil(n / m))

        basic_conf["m"] = m
        basic_conf["U"] = U
        basic_conf["instance"] = "TSPLIB/{}.tsp".format(ins)

        curr_line = "{},{},{},{},".format(ins, n, m, U)

         # karabulut
        outputsolver = "{}/karabulut-{}-{}.json".format(output_folder, ins, m)
        conf = basic_conf.copy()
        conf["IP"] = "karabulut"
        conf["IQP"] = False
        conf["outputFile"] = outputsolver

        with open(jsoninputname, "w") as write_file:
            json.dump(conf, write_file, indent=4)
        os.system("python main.py {}".format(jsoninputname))

        jsonoutput = parse_input_file(outputsolver)
        objval = jsonoutput["OUTPUT"]["objval"]
        timeinc = jsonoutput["OUTPUT"]["timeinc"]
        curr_line += "{},{},".format(objval, timeinc)

        # IQP1
        outputsolver = "{}/IQP1-{}-{}.json".format(output_folder, ins, m)
        conf = basic_conf.copy()
        conf["IP"] = "IP1"
        conf["IQP"] = True
        conf["outputFile"] = outputsolver

        with open(jsoninputname, "w") as write_file:
            json.dump(conf, write_file, indent=4)
        os.system("python main.py {}".format(jsoninputname))

        jsonoutput = parse_input_file(outputsolver)
        objval = jsonoutput["OUTPUT"]["objval"]
        timeinc = jsonoutput["OUTPUT"]["timeinc"]
        curr_line += "{},{},".format(objval, timeinc)

        # ILP1
        outputsolver = "{}/ILP1-{}-{}.json".format(output_folder, ins, m)
        conf = basic_conf.copy()
        conf["IP"] = "IP1"
        conf["IQP"] = False
        conf["outputFile"] = outputsolver

        with open(jsoninputname, "w") as write_file:
            json.dump(conf, write_file, indent=4)
        os.system("python main.py {}".format(jsoninputname))

        jsonoutput = parse_input_file(outputsolver)
        objval = jsonoutput["OUTPUT"]["objval"]
        timeinc = jsonoutput["OUTPUT"]["timeinc"]
        curr_line += "{},{},".format(objval, timeinc)

        # IQP2
        outputsolver = "{}/IQP2-{}-{}.json".format(output_folder, ins, m)
        conf = basic_conf.copy()
        conf["IP"] = "IP2"
        conf["IQP"] = True
        conf["outputFile"] = outputsolver

        with open(jsoninputname, "w") as write_file:
            json.dump(conf, write_file, indent=4)
        os.system("python main.py {}".format(jsoninputname))

        jsonoutput = parse_input_file(outputsolver)
        objval = jsonoutput["OUTPUT"]["objval"]
        timeinc = jsonoutput["OUTPUT"]["timeinc"]
        curr_line += "{},{},".format(objval, timeinc)

        # ILP2
        outputsolver = "{}/ILP2-{}-{}.json".format(output_folder, ins, m)
        conf = basic_conf.copy()
        conf["IP"] = "IP2"
        conf["IQP"] = False
        conf["outputFile"] = outputsolver

        with open(jsoninputname, "w") as write_file:
            json.dump(conf, write_file, indent=4)
        os.system("python main.py {}".format(jsoninputname))

        jsonoutput = parse_input_file(outputsolver)
        objval = jsonoutput["OUTPUT"]["objval"]
        timeinc = jsonoutput["OUTPUT"]["timeinc"]
        curr_line += "{},{}\n".format(objval, timeinc)

        # write results of all solvers
        with open("{}/{}".format(output_folder, output_path), "a") as results_file:
            results_file.write(curr_line)
