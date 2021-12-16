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
from datetime import datetime
from visualizer import plots
from common.simulation import World, Simulation
from common.serialization import Log
from common.charger_waiting_estimation import getChargerWaitingTimeEstimation


def run(args):

    # Fix random seeds
    import random
    import numpy as np
    import tensorflow as tf
    random.seed(args.seed)
    np.random.seed(args.seed)
    tf.random.set_seed(args.seed)

    yamlFile = open(args.source, 'r')
    yamlObject = load(yamlFile, Loader=Loader)

    yamlFileName = os.path.splitext(os.path.basename(args.source))[0]

    conf = yamlObject
    world = World(conf)

    folder = f"results\\{args.output}\\{args.queue_type}"
    estFolder = f"{folder}\\{args.waiting_estimation}"
    if not os.path.exists(estFolder):
        os.makedirs(estFolder)
    
    if not os.path.exists(f"{folder}\\animations"):
        os.makedirs(f"{folder}\\animations")

    if not os.path.exists(f"{folder}\\charger_logs"):
        os.makedirs(f"{folder}\\charger_logs")

    totalLog = Log([
        'Active Drones',
        'Total Damage',
        'Energy Consumed',
    ])

    estimation = getChargerWaitingTimeEstimation(world, args, outputFolder=estFolder)
    verbose = int(args.verbose)

    for t in range(args.train):
        if verbose > 0:
            print(f"Iteration {t + 1} started at {datetime.now()}: ")

        for i in range(args.number):
            if verbose > 1:
                print(f"    Run {i + 1} started at {datetime.now()}: ")

            currentWorld = copy.deepcopy(world)
            newSimulation = Simulation(currentWorld, folder, visualize=args.animation)
            estimation, newLog = newSimulation.run(f"{yamlFileName}_{str(t + 1)}_{str(i + 1)}", estimation, verbose, args)


            totalLog.register(newLog)

        estimation.endIteration()

    estimation.save()

    totalLog.export(f"{folder}\\log_{args.waiting_estimation}.csv")
    if args.chart:
        plots.createLogPlot(
            totalLog.records,
            f"{folder}\\{yamlFileName}.png",
            f"World: {yamlFileName}\nEstimator: {estimation.name}\nQueue Type: {args.queue_type}",
            (args.number,args.train))


def main():
    parser = argparse.ArgumentParser(description='Process YAML source file (S) and run the simulation (N) Times with Model M.')
    parser.add_argument('source', metavar='source', type=str, help='YAML address to be run.')
    parser.add_argument('-n', '--number', type=int, help='the number of simulation runs per training.', required=False, default="1")
    parser.add_argument('-o', '--output', type=str, help='the output folder', required=False, default="output")
    parser.add_argument('-t', '--train', type=int, help='the number of trainings to be performed.', required=False, default="1")
    parser.add_argument('-v', '--verbose', type=int, help='the verboseness between 0 and 4.', required=False, default="0")
    parser.add_argument('-a', '--animation', action='store_true', default=False, help='toggles saving the final results as a GIF animation.')
    parser.add_argument('-c', '--chart', action='store_true', default=False, help='toggles saving the final results as a PNG chart.')
    parser.add_argument('-w', '--waiting_estimation', type=str, choices=["baseline_zero", "neural_network", "queue_missing_battery", "queue_charging_time"], help='The estimation model to be used for predicting charger waiting time.', required=False, default="neural_network")
    parser.add_argument('-q', '--queue_type', type=str, choices=["fifo", "priority"], help='Charging waiting queue.', required=False, default="fifo")
    parser.add_argument('--test_split', type=float, help='Number of records used for evaluation.', required=False, default=0.2)
    parser.add_argument('--hidden_layers', nargs="+", type=int, default=[20], help='Number of neurons in hidden layers.')
    parser.add_argument('-s', '--seed', type=int, help='Random seed.', required=False, default=42)
    args = parser.parse_args()

    number = args.number

    if number <= 0:
        raise argparse.ArgumentTypeError(f"{number} is an invalid positive int value")

    run(args)


if __name__ == "__main__":
    main()
