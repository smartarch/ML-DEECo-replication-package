""" 
    This file contains a simple experiment run
"""
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

import os
import argparse
import copy

from visualizer import plots
from common.simulation import World, Simulation
from common.serialization import Log

def run(args):
    yamlFile = open(args.source, 'r')
    yamlObject = load(yamlFile, Loader=Loader)
    
    yamlFileName = os.path.splitext(os.path.basename(args.source))[0]
    
    conf = yamlObject
    world = World(conf)


    folder = f"results\\{args.output}"
    if not os.path.exists(folder):
            os.makedirs(folder)
    log = Log([
        'Active Drones',
        'Total Damage',
        'Energy Consumed',
    ])

    model = None

    for i in range(args.number):
        currentWorld = copy.deepcopy(world)
        newSimulation = Simulation(currentWorld,folder, visualize=args.animation)
        model, newLog = newSimulation.run(yamlFileName+str(i+1),model)
        log.register(newLog)

    log.export(f"{folder}\\{yamlFileName}.csv")
    if args.chart == True:
        plots.createLogPlot(log.records,f"{folder}\\{yamlFileName}.png")

def main():
    parser = argparse.ArgumentParser(description='Process YAML source file (S) and run the simulation (N) Times with Model M.')
    parser.add_argument('source', metavar='source', type=str, help='YAML address to be run.')
    parser.add_argument('-n','--number', type=int, help='the number of simulation runs (positive int).', required=False, default="1")
    parser.add_argument('-o','--output', type=str, help='the output folder', required=False, default="output")
    parser.add_argument('-m','--model',  choices=['time', 'energy', 'protection'], type=str, help='the model name', required=False, default="time")
    parser.add_argument('-a','--animation', action='store_true',default=False,help='toggles saving the final results as a GIF animation.')
    parser.add_argument('-c','--chart', action='store_true',default=False,help='toggles saving the final results as a PNG chart.')
    args = parser.parse_args()
    
    number = args.number

    if number <= 0:
        raise argparse.ArgumentTypeError(f"{number} is an invalid positive int value")
    

    run(args)


if __name__ == "__main__":
    main()
