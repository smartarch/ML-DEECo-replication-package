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
import math
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")  # Report only TF errors by default
# os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Disable GPU in TF. The models are small, so it is actually faster to use the CPU.
import tensorflow as tf
from simulation.world import WORLD, ENVIRONMENT  # This import should be first
from estimators.estimator import ConstantEstimator, NeuralNetworkEstimator, NoEstimator
from simulation.simulation import Simulation
from utils import plots
from utils.serialization import Log
from utils.verbose import setVerboseLevel, verbosePrint
import importlib
def run(args):

    # Fix random seeds
    random.seed(args.seed)
    np.random.seed(args.seed)
    tf.random.set_seed(args.seed)

    # Set number of threads
    tf.config.threading.set_inter_op_parallelism_threads(args.threads)
    tf.config.threading.set_intra_op_parallelism_threads(args.threads)

    # load config from yaml
    yamlFile = open(args.input, 'r')
    yamlObject = load(yamlFile, Loader=Loader)

    def findChargerCapacity(yamlObject):
        margin = 1.3
        chargers = len(yamlObject['chargers'])
        drones = yamlObject['drones']
        
        c1 = yamlObject['chargingRate']
        c2 = yamlObject['droneMovingEnergyConsumption'] 
 
        return math.ceil( 
            (margin*drones*c2)/((chargers*c1)+(chargers*margin*c2))
        )

    #yamlObject['drones']=drones
    if args.birds > 0:
        yamlObject['birds']=args.birds
    #yamlObject['maxSteps']=int(args.timesteps)
    yamlObject['chargerCapacity']= findChargerCapacity(yamlObject)
    yamlObject['totalAvailableChargingEnergy']= min(
                yamlObject['chargerCapacity']*len(yamlObject['chargers'])*yamlObject['chargingRate'],
                yamlObject['totalAvailableChargingEnergy'])
    
    ENVIRONMENT.loadConfig(yamlObject)
    # prepare folder structure for results
    yamlFileName = os.path.splitext(os.path.basename(args.input))[0]

    folder = f"results\\{args.output}"
    estWaitingFolder = f"{folder}\\{args.waiting_estimation}"

    if not os.path.exists(f"{folder}\\animations"):
        os.makedirs(f"{folder}\\animations")

    if not os.path.exists(f"{folder}\\charger_logs"):
        os.makedirs(f"{folder}\\charger_logs")

    totalLog = Log([
        'Active Drones',
        'Total Damage',
        'Alive Drone Rate',
        'Damage Rate',
        'Charger Capacity',
        'Train',
        'Run',
        'Charge Alert',
        'Battery Random Reduction'
    ])

    averageLog = Log([
        'Active Drones',
        'Total Damage',
        'Alive Drone Rate',
        'Damage Rate',
        'Charger Capacity',
        'Train',
        'Average Run',
        'Charge Alert',
        'Battery Random Reduction'
    ])

    # create the estimators
    waitingTimeEstimatorArgs = {
        "outputFolder": estWaitingFolder,
        "args": args,
        "name": "Waiting Time",
    }
    if args.waiting_estimation == "baseline":
        waitingTimeEstimator = ConstantEstimator(args.baseline, **waitingTimeEstimatorArgs)
    else:
        waitingTimeEstimator = NeuralNetworkEstimator(
            args.hidden_layers,
            fit_params={
                "batch_size": 256,
            },
            **waitingTimeEstimatorArgs
        )
        if args.load != "":
            waitingTimeEstimator.loadModel(args.load)

    if args.examples:
        fit_params = {
            "epochs": 20,
        }
        droneBatteryEstimator = NeuralNetworkEstimator(
            hidden_layers=[32, 32], fit_params=fit_params,
            outputFolder=f"{folder}\\drone_battery", args=args, name="Drone Battery"
        )
        chargerUtilizationEstimator = NeuralNetworkEstimator(
            hidden_layers=[32, 32], fit_params=fit_params,
            outputFolder=f"{folder}\\charger_utilization", args=args, name="Charger Capacity"
        )
        chargerFullEstimator = NeuralNetworkEstimator(
            hidden_layers=[32, 32], fit_params=fit_params,
            outputFolder=f"{folder}\\charger_full", args=args, name="Charger Full"
        )
        droneStateEstimator = NeuralNetworkEstimator(
            hidden_layers=[32, 32], fit_params=fit_params,
            outputFolder=f"{folder}\\drone_state", args=args, name="Drone State"
        )
        timeToChargingEstimator = NeuralNetworkEstimator(
            hidden_layers=[32, 32], fit_params=fit_params,
            outputFolder=f"{folder}\\drone_time_to_charging", args=args, name="Time To Charging"
        )
        timeToLowBatteryEstimator = NeuralNetworkEstimator(
            hidden_layers=[32, 32], fit_params=fit_params,
            outputFolder=f"{folder}\\drone_time_to_low_battery", args=args, name="Time To Low Battery"
        )
    else:
        droneBatteryEstimator = NoEstimator(
            args=args, name="Drone Battery"
        )
        chargerUtilizationEstimator = NoEstimator(
            args=args, name="Charger Capacity"
        )
        chargerFullEstimator = NoEstimator(
            args=args, name="Charger Full"
        )
        droneStateEstimator = NoEstimator(
            args=args, name="Drone State"
        )
        timeToChargingEstimator = NoEstimator(
            args=args, name="Time To Charging"
        )
        timeToLowBatteryEstimator = NoEstimator(
            args=args, name="Time To Low Battery"
        )

    WORLD.waitingTimeEstimator = waitingTimeEstimator
    WORLD.droneBatteryEstimator = droneBatteryEstimator
    WORLD.chargerUtilizationEstimator = chargerUtilizationEstimator
    WORLD.chargerFullEstimator = chargerFullEstimator
    WORLD.droneStateEstimator = droneStateEstimator
    WORLD.timeToChargingEstimator = timeToChargingEstimator
    WORLD.timeToLowBatteryEstimator = timeToLowBatteryEstimator

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
        # calculate the average rate

        averageLog.register(totalLog.average(t*args.number, (t+1)*args.number))

        for estimator in WORLD.estimators:
            estimator.endIteration()
            estimator.saveModel(t + 1)

    totalLog.export(f"{folder}\\{yamlFileName}_{args.waiting_estimation}.csv")
    averageLog.export(f"{folder}\\{yamlFileName}_{args.waiting_estimation}_average.csv")
    if args.chart:
        plots.createLogPlot(
            totalLog.records,
            averageLog.records,
            f"{folder}\\{yamlFileName}_{args.waiting_estimation}.png",
            f"World: {yamlFileName}\nEstimator: {waitingTimeEstimator.estimatorName}",
            (args.number, args.train)
        )
    return averageLog





def main():
    parser = argparse.ArgumentParser(description='Process YAML source file (S) and run the simulation (N) Times with Model M.')
    parser.add_argument('input', type=str, help='YAML address to be run.')
    parser.add_argument('-x', '--birds', type=int, help='A number of birds',required=True)
    parser.add_argument('-n', '--number', type=int, help='the number of simulation runs per training.', required=False, default="0")
    parser.add_argument('-o', '--output', type=str, help='the output folder', required=False, default="output")
    parser.add_argument('-t', '--train', type=int, help='the number of trainings to be performed.', required=False, default="1")
    parser.add_argument('-v', '--verbose', type=int, help='the verboseness between 0 and 4.', required=False, default="0")
    parser.add_argument('-a', '--animation', action='store_true', default=False,
                        help='toggles saving the final results as a GIF animation.')
    parser.add_argument('-c', '--chart', action='store_true', default=False, help='toggles saving the final results as a PNG chart.')
    parser.add_argument('-w', '--waiting_estimation', type=str,
                        # choices=["baseline_zero", "neural_network", "queue_missing_battery", "queue_charging_time"],
                        choices=["baseline", "neural_network"],
                        help='The estimation model to be used for predicting charger waiting time.', required=False,
                        default="neural_network")
    parser.add_argument('-d', '--accumulate_data', action='store_true', default=False, help='False = use only training data from last iteration.\nTrue = accumulate training data from all previous iterations.')
    parser.add_argument('--test_split', type=float, help='Number of records used for evaluation.', required=False, default=0.2)
    parser.add_argument('--hidden_layers', nargs="+", type=int, default=[256, 256], help='Number of neurons in hidden layers.')
    parser.add_argument('-s', '--seed', type=int, help='Random seed.', required=False, default=42)
    parser.add_argument('-b', '--baseline', type=int, help='Constant for baseline.', required=False, default=0)
    parser.add_argument('-l', '--load', type=str, help='Load Model.', required=False, default="")
    parser.add_argument('-e', '--examples', action='store_true', default=False, help='Additional examples for debug purposes.')
    parser.add_argument('--threads', type=int, help='Number of CPU threads TF can use.', required=False, default=4)
    args = parser.parse_args()

    number = args.number
    setVerboseLevel(args.verbose)

    if number <= 0:
        raise argparse.ArgumentTypeError(f"{number} is an invalid positive int value")

    run(args)

if __name__ == "__main__":
    main()