""" 
    This file contains a simple experiment run
"""
import json
import sys
sys.path.insert(0, 'D:\\CUNI\\Task 2 - CPaper\\Project Files\\en2\\en2-drone-charging')

import os
from source.simulation import World


DEFAULT_CONFIGURE ={
    'drones': 5,
    'chargers': [
        [0.4,0.4],
        [0.6,0.6],
    ],
    'birds': 5,
    'places': [
        [0.1,0.1,0.3,0.3], # a square top-lef -> (0.1,0.1) and bottom-right -> (0.3,0.3)
        [0.6,0.6,0.8,0.8], 
    ],
    'time_steps':10
}

def run (jsonFileAddress):

    conf = DEFAULT_CONFIGURE.copy()
    jsonFile = open(jsonFileAddress,)
    compiledJson = json.load(jsonFile)
    # copies the configuration file to the the local configuration
    for jsonElement in compiledJson:
        if jsonElement in conf:
            conf[jsonElement] = compiledJson[jsonElement]

    w = World(conf)
    w.run()



def main():
    # print command line arguments
    if len(sys.argv)<=1:
        run ("experiments/exp1.json")


    for arg in sys.argv[1:]:
        if (os.path.isfile(arg)):
            run (arg)
        else:
            print(f"{arg} does not exists")

if __name__ == "__main__":
    main()