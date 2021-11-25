""" 
    This file contains a simple experiment run
"""
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

import argparse
from common.simulation import World, Simulation

def run (yamlFileAddress,showAnimation):
    yamlFile = open(yamlFileAddress,'r')
    yamlObject = load(yamlFile,Loader=Loader)
    conf = yamlObject
    currentWorld = World(conf)
    newSimulation = Simulation(currentWorld,visualize=showAnimation)
    newSimulation.run(yamlFileAddress.split('\\')[-1].split('.')[0])

   


def main():
    parser = argparse.ArgumentParser(description='Process YAML files and run the simulation.')
    parser.add_argument('yamlFiles', metavar='S', type=str, nargs='+',
                    help='A list of YAML filenames to be run')

    parser.add_argument('--animation', action='store_true')
    args = parser.parse_args()
    for yamlFileAddress in args.yamlFiles:
        run (yamlFileAddress,showAnimation=args.animation)


if __name__ == "__main__":
    main()