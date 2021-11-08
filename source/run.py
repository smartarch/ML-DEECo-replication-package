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