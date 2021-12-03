""" 
    This file contains a simple experiment run
"""
from yaml import load, dump

from common.charger_waiting_estimation import getChargerWaitingTimeEstimation

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

    estimation = getChargerWaitingTimeEstimation(world, args.waiting_estimation, outputFolder=folder)

    verbose = int(args.verbose)

    for t in range(args.train):
        if verbose > 0:
            print(f"Train {t + 1} Started at {datetime.now()}: ")

        for i in range(args.number):
            if verbose > 1:
                print(f"    Run {i + 1} Started at {datetime.now()}: ")

            currentWorld = copy.deepcopy(world)
            newSimulation = Simulation(currentWorld, folder, visualize=args.animation)
            estimation, newLog = newSimulation.run(f"{yamlFileName}_{str(t + 1)}_{str(i + 1)}", estimation, verbose)
            log.register(newLog)

        estimation.endIteration(t)

    estimation.save()

    log.export(f"{folder}\\{yamlFileName}.csv")
    if args.chart == True:
        plots.createLogPlot(log.records, f"{folder}\\{yamlFileName}.png")


def main():
    parser = argparse.ArgumentParser(description='Process YAML source file (S) and run the simulation (N) Times with Model M.')
    parser.add_argument('source', metavar='source', type=str, help='YAML address to be run.')
    parser.add_argument('-n', '--number', type=int, help='the number of simulation runs per training.', required=False, default="1")
    parser.add_argument('-o', '--output', type=str, help='the output folder', required=False, default="output")
    parser.add_argument('-t', '--train', type=int, help='the number of trainings to be performed.', required=False, default="1")
    parser.add_argument('-v', '--verbose', type=int, help='the verboseness between 0 and 4.', required=False, default="0")
    parser.add_argument('-a', '--animation', action='store_true', default=False,
                        help='toggles saving the final results as a GIF animation.')
    parser.add_argument('-c', '--chart', action='store_true', default=False, help='toggles saving the final results as a PNG chart.')
    parser.add_argument('-w', '--waiting_estimation', type=str, choices=["baseline_zero", "neural_network"], help='The estimation model to be used for predicting charger waiting time.', required=False, default="neural_network")
    args = parser.parse_args()

    number = args.number

    if number <= 0:
        raise argparse.ArgumentTypeError(f"{number} is an invalid positive int value")

    run(args)


if __name__ == "__main__":
    main()
