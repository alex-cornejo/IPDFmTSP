# This work is licensed under CC BY-NC 4.0 
# Authors: Cornejo-Acosta, J.A.; Garcia-Diaz, J.; Perez-Sansalvador, J.C.; Segura, C. 

import json
import sys

from IP1 import run_IP1
from IP2 import run_IP2
from karabulut import run_karabulut

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise Exception("Wrong number of arguments!")

    conf_file = sys.argv[1]
    with open(conf_file) as user_file:
        file_contents = user_file.read()

    conf = json.loads(file_contents)

    if conf["IP"] == "karabulut":
        run_karabulut(conf)
    elif conf["IP"] == "IP1":
        run_IP1(conf)
    elif conf["IP"] == "IP2":
        run_IP2(conf)
    else:
        raise Exception("Wrong formulation!")
