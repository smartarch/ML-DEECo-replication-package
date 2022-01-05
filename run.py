""" 
    This file contains a simple experiment run
"""
from yaml import load
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

import os
import argparse
from datetime import datetime
import random
import numpy as np

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")  # Report only TF errors by default
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Disable GPU in TF. The models are small, so it is actually faster to use the CPU.
import tensorflow as tf

from simulation.world import WORLD, ENVIRONMENT  # This import should be first
from estimators.estimator import ConstantEstimator, NeuralNetworkEstimator
from simulation.simulation import Simulation
from utils import plots
from utils.serialization import Log
from utils.verbose import setVerboseLevel, verbosePrint


def run(args):
    # Fix random seeds
    random.seed(args.seed)
    np.random.seed(args.seed)
    tf.random.set_seed(args.seed)

    # load config from yaml
    yamlFile = open(args.source, 'r')
    yamlObject = load(yamlFile, Loader=Loader)
    ENVIRONMENT.loadConfig(yamlObject)

    # prepare folder structure for results
    yamlFileName = os.path.splitext(os.path.basename(args.source))[0]

    folder = f"results\\{args.output}"
    estWaitingFolder = f"{folder}\\{args.waiting_estimation}"
    estDroneFolder = f"{folder}\\drone_battery"
    estChargerUtilFolder = f"{folder}\\charger_utilization"
    estChargerFullFolder = f"{folder}\\charger_full"

    if not os.path.exists(f"{folder}\\animations"):
        os.makedirs(f"{folder}\\animations")

    if not os.path.exists(f"{folder}\\charger_logs"):
        os.makedirs(f"{folder}\\charger_logs")

    totalLog = Log([
        'Train',
        'Run',
        'Active Drones',
        'Total Damage',
        'Energy Consumed',
    ])

    # create the estimators
    waitingTimeEstimatorArgs = {
        "outputFolder": estWaitingFolder,
        "args": args,
        "name": "Waiting Time",
    }
    if args.waiting_estimation == "baseline_zero":
        waitingTimeEstimator = ConstantEstimator(**waitingTimeEstimatorArgs)
    else:
        waitingTimeEstimator = NeuralNetworkEstimator(
            args.hidden_layers,
            **waitingTimeEstimatorArgs
        )

    if args.examples:
        droneBatteryEstimator = NeuralNetworkEstimator(
            hidden_layers=[32, 32],
            activation=tf.keras.activations.sigmoid,  # We want a value between 0 and 1
            outputFolder=estDroneFolder, args=args, name="Drone Battery"
        )
    else:
        droneBatteryEstimator = ConstantEstimator(outputFolder=estDroneFolder, args=args, name="Drone Battery")

    if args.examples:
        chargerUtilizationEstimator = NeuralNetworkEstimator(
            hidden_layers=[32, 32],
            outputFolder=estChargerUtilFolder, args=args, name="Charger Capacity"
        )
    else:
        chargerUtilizationEstimator = ConstantEstimator(outputFolder=estChargerUtilFolder, args=args, name="Charger Capacity")

    if args.examples:
        chargerFullEstimator = NeuralNetworkEstimator(
            hidden_layers=[32, 32],
            outputFolder=estChargerFullFolder, args=args, name="Charger Full"
        )
    else:
        chargerFullEstimator = ConstantEstimator(outputFolder=estChargerFullFolder, args=args, name="Charger Full")

    WORLD.waitingTimeEstimator = waitingTimeEstimator
    WORLD.droneBatteryEstimator = droneBatteryEstimator
    WORLD.chargerUtilizationEstimator = chargerUtilizationEstimator
    WORLD.chargerFullEstimator = chargerFullEstimator

    # start the main loop
    for t in range(args.train):
        verbosePrint(f"Iteration {t + 1} started at {datetime.now()}:", 1)

        for i in range(args.number):
            verbosePrint(f"Run {i + 1} started at {datetime.now()}:", 2)

            WORLD.reset()
            simulation = Simulation(folder, visualize=args.animation)
            newLog, chargerLogs = simulation.run(yamlFileName,t,i, args)

            if args.chart:
                verbosePrint(f"Saving charger plot...", 3)
                plots.createChargerPlot(
                    chargerLogs,
                    f"{folder}\\charger_logs\\{yamlFileName}_{str(t + 1)}_{str(i + 1)}",
                    f"World: {yamlFileName}\nEstimator: {waitingTimeEstimator.estimatorName}\n Run: {i + 1} in training {t + 1}\nCharger Queues")
                verbosePrint(f"Charger plot saved.", 3)
            totalLog.register(newLog)

        for estimator in WORLD.estimators:
            estimator.endIteration()

    for estimator in WORLD.estimators:
        estimator.saveModel()

    totalLog.export(f"{folder}\\{yamlFileName}_{args.waiting_estimation}.csv")
    if args.chart:
        plots.createLogPlot(
            totalLog.records,
            f"{folder}\\{yamlFileName}_{args.waiting_estimation}.png",
            f"World: {yamlFileName}\nEstimator: {waitingTimeEstimator.estimatorName}",
            (args.number, args.train)
        )


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
    parser.add_argument('-w', '--waiting_estimation', type=str,
                        # choices=["baseline_zero", "neural_network", "queue_missing_battery", "queue_charging_time"],
                        choices=["baseline_zero", "neural_network"],
                        help='The estimation model to be used for predicting charger waiting time.', required=False,
                        default="neural_network")
    # parser.add_argument('-q', '--queue_type', type=str, choices=["fifo", "priority"], help='Charging waiting queue.', required=False,
    #                     default="fifo")
    parser.add_argument('--test_split', type=float, help='Number of records used for evaluation.', required=False, default=0.2)
    parser.add_argument('--hidden_layers', nargs="+", type=int, default=[256, 256], help='Number of neurons in hidden layers.')
    parser.add_argument('-s', '--seed', type=int, help='Random seed.', required=False, default=42)
    # TODO(MT): remove?
    parser.add_argument('-e', '--examples', action='store_true', default=False, help='Additional examples for debug purposes.')
    args = parser.parse_args()

    number = args.number
    setVerboseLevel(args.verbose)

    if number <= 0:
        raise argparse.ArgumentTypeError(f"{number} is an invalid positive int value")

    run(args)


if __name__ == "__main__":
    main()
