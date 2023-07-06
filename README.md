<p xmlns:cc="http://creativecommons.org/ns#" >This work is licensed under <a href="http://creativecommons.org/licenses/by-nc/4.0/?ref=chooser-v1" target="_blank" rel="license noopener noreferrer" style="display:inline-block;">CC BY-NC 4.0<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1"><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1"><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/nc.svg?ref=chooser-v1"></a></p>

# Compact Integer Programs for Depot-Free Multiple Traveling Salesperson Problems

## Citing
### BibTex
```
@Article{Cornejo-Acosta2023,
AUTHOR = {Cornejo-Acosta, José Alejandro and García-Díaz, Jesús and Pérez-Sansalvador, Julio César and Segura, Carlos},
TITLE = {Compact Integer Programs for Depot-Free Multiple Traveling Salesperson Problems},
JOURNAL = {Mathematics},
VOLUME = {11},
YEAR = {2023},
NUMBER = {13},
ARTICLE-NUMBER = {3014},
URL = {https://www.mdpi.com/2227-7390/11/13/3014},
ISSN = {2227-7390},
DOI = {10.3390/math11133014}
}
```


**If this implementation is useful for you, please cite our paper.**

This repository contains the following integer programs for the $\text{DF}m\text{TSP}$.

| Formulation | Reference                   | variables | constraints                           |
|-------------|-----------------------------|-----------|---------------------------------------|
| IP1         | Cornejo-Acosta et al. 2023  | $O(n^2m)$ | $O(n^2)$ for IQP, $O(n^2m)$ for ILP   |
| IP2         | Cornejo-Acosta et al. 2023  | $O(n^2)$  | $O(n^2)$ for IQP, $O(n^2m)$ for ILP   |
| karabulut   | Karabulut et al. 2021       | $O(n^2m)$ | $O(n^2)$                              |

IP1 and IP2 are formulations based in the concept of dummy depots.

### NOTE: These instructions assume gurobi for python is installed with a valid license.

## Running

```
python main.py [intput.json]
```
where `intput.json` is a configuration json file of the form:
```
{
  "IP": "IP1",
  "instance": "TSPLIB/burma14.tsp",
  "m": 3,
  "L": 2,
  "U": 5,
  "objective": "minsum",
  "variant": "OP",
  "R": [],
  "IQP": true,
  "outputFile": "output1.json",
  "MemLimit": 12,
  "TimeLimit": 60,
  "presolve": -1,
  "MIPGap": 0,
  "outputFlag": 1
}
```
### Where,

| Parameter      | Description                                                                                                         |
|----------------|---------------------------------------------------------------------------------------------------------------------|
| `[IP]`         | (string) Formulation to be executed (**karabulut**, **IP1** or **IP2**).                                            |
| `[instance]`   | (string) TSPLIB instance.                                                                                           |
| `[m]`          | (integer) Number of salespersons.                                                                                   |
| `[L]`          | (integer) Lower bound constraint (minimum number of vertices each salesperson can visit).                           |
| `[U]`          | (integer) Upper bound constraint (maximum number of vertices each salesperson can visit).                           |
| `[objective]`  | (string) Objective function to optimize (**minsum** or **minmax**).                                                 |
| `[variant]`    | (string) Variant of paths **CP**(closed-paths) or **OP** (open-pats), the latter is available only for IP1 and IP2. |
| `[R]`          | (list) Set of actual depots (available only for IP1 and IP2).                                                       |
| `[IQP]`        | (bool) **false** if objective function is desired to be linear (available only for IP1).                            |
| `[outputFile]`        | (string) Output file to print the found solution and results.                           |
| `[MemLimit]`   | (integer) Memory limit in GB (it is a gurobi parameter).                                                            |
| `[TimeLimit]`  | (integer) Time limit in seconds (it is a gurobi parameter).                                                         |
| `[presolve]`   | (integer) presolve desired (it is a gurobi parameter).                                                              |
| `[MIPGap]`     | (float) gap desired (it is a gurobi parameter).                                                                     |
| `[outputFlag]` | (integer) log level (it is a gurobi parameter).                                                                     |

All of these parameters are a must.<br/>
NOTE: For IP2, bounding constraints will be used only when $2 \leq L \leq U \leq n$ holds.
<br/>
The output will be printed in the specified file in `outputFile`
## Example of output 1
```
{
    "INPUT": {
        "IP": "IP1",
        "outputFile": "output1.json",
        "instance": "TSPLIB/burma14.tsp",
        "m": 3,
        "L": 2,
        "U": 5,
        "IQP": true,
        "R": [],
        "objective": "minsum",
        "variant": "OP",
        "MemLimit": 12,
        "TimeLimit": 60,
        "presolve": -1,
        "MIPGap": 0,
        "outputFlag": 1
    },
    "OUTPUT": {
        "objval": "2104.0",
        "runtime": 0.8590571880340576,
        "gap": "0.0",
        "timeinc": "0.33600401878356934",
        "paths": [
            [0, 7, 10, 8, 9],
            [1, 13, 2, 3],
            [4, 5, 11, 6, 12]
        ],
        "convergence": [
            [0.02774214744567871, 3042.0],
            [0.02958512306213379, 2688.0],
            [0.041274070739746094, 2253.0],
            [0.11742901802062988, 2190.0],
            [0.13790011405944824, 2128.0],
            [0.33600401878356934, 2104.0]
        ]
    }
}
```
where <br/>
`INPUT` section specifies the input parameters. <br/>
`default` specifies the input parameters that were automatically changed to a default value. <br/>
`OUTPUT` section shows results of the running. <br/>
`objval` is the best found solution objective value. <br/>
`timeinc` time taken to reach the incumbent. <br/>
`paths` salespersons' paths (indexed from 0). <br/>
`convergence` convergence of solution reported by Gurobi, list of pairs $(time, objval)$. <br/>
`IGNORED_PARAMETERS` shows the input parameters that were not used (if exist). <br/>

## Example of input 2
```
{
  "IP": "karabulut",
  "instance": "TSPLIB/burma14.tsp",
  "m": 2,
  "L": 2,
  "U": 7,
  "objective": "minsum",
  "variant": "OP",
  "IQP": true,
  "outputFile": "output2.json",
  "MemLimit": 12,
  "TimeLimit": 60,
  "presolve": 2,
  "MIPGap": 0,
  "outputFlag": 1
}
```

## Example of output 2
```
{
    "INPUT": {
        "IP": "karabulut",
        "outputFile": "output.txt",
        "instance": "TSPLIB/burma14.tsp",
        "m": 2,
        "L": 2,
        "U": 7,
        "objective": "minsum",
        "variant": "CP",
        "MemLimit": 12,
        "TimeLimit": 60,
        "presolve": 2,
        "MIPGap": 0,
        "outputFlag": 1,
        "default": [
            "variant"
        ]
    },
    "IGNORED_PARAMETERS": {
        "variant": "OP",
        "IQP": true
    },
    "OUTPUT": {
        "objval": "3414.0",
        "runtime": 15.598864793777466,
        "gap": "0.0",
        "timeinc": "0.8360719680786133",
        "paths": [
            [0, 7, 12, 10, 8, 9, 1],
            [2, 3, 4, 5, 11, 6, 13]
        ],
        "convergence": [
            [0.4253249168395996, 3901.0],
            [0.43735194206237793, 3705.0],
            [0.47217893600463867, 3552.0],
            [0.5277419090270996, 3522.0],
            [0.8360719680786133, 3414.0]
        ]
    }
}
```
Note that the `variant` parameter was automatically changed to `CP` because it is the only one available for *karabulut* formulation, and the `IQP` parameter was ignored because it is not available for *karabulut* formulation.

# Contact
* jesus.garcia@conahcyt.mx
* alexcornejo@inaoep.mx
