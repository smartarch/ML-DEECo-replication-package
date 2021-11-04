""" 
    This file contains a simple experiment run
"""
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

import argparse
import simulation


DEFAULT_CONFIGURE ={
    'drones': 5,
    'chargers': [
        [0.4,0.4],
        [0.6,0.6],
    ],
    'birds': 5,
    'fields': [
        [0.1,0.1,0.3,0.3], # a square top-lef -> (0.1,0.1) and bottom-right -> (0.3,0.3)
        [0.6,0.6,0.8,0.8], 
    ],
    'maxTimeSteps':100,
    'gridCellSize': [0.01,0.01]
}

def run (yamlFileAddress):
    yamlFile = open(yamlFileAddress,'r')
    yamlObject = load(yamlFile,Loader=Loader)
    conf = yamlObject
    simulation.currentWorld = simulation.World(conf)
    newSimulation = simulation.Simulation()
    newSimulation.run()

   


def main():
    parser = argparse.ArgumentParser(description='Process YAML files and run the simulation.')
    parser.add_argument('yamlFiles', metavar='S', type=str, nargs='+',
                    help='A list of YAML filenames to be run')
    args = parser.parse_args()
    for yamlFileAddress in args.yamlFiles:
        run (yamlFileAddress)


if __name__ == "__main__":
    main()