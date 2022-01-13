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
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Disable GPU in TF. The models are small, so it is actually faster to use the CPU.
import tensorflow as tf
from simulation.world import WORLD, ENVIRONMENT  # This import should be first
from estimators.estimator import ConstantEstimator, NeuralNetworkEstimator
from simulation.simulation import Simulation
from utils import plots
from utils.serialization import Log
from utils.verbose import setVerboseLevel, verbosePrint
import importlib
def run(args,drones,birds):

    # Fix random seeds
    random.seed(args.seed)
    np.random.seed(args.seed)
    tf.random.set_seed(args.seed)

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

    yamlObject['drones']=drones
    yamlObject['birds']=birds
    yamlObject['chargerCapacity']=findChargerCapacity(yamlObject)
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
        'Average Active Drones',
        'Average Total Damage',
        'Average Alive Drone Rate',
        'Average Damage Rate',
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
    if args.waiting_estimation == "baseline_zero":
        waitingTimeEstimator = ConstantEstimator(**waitingTimeEstimatorArgs)
    else:
        waitingTimeEstimator = NeuralNetworkEstimator(
            args.hidden_layers,
            **waitingTimeEstimatorArgs
        )

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
        droneBatteryEstimator = ConstantEstimator(
            outputFolder=f"{folder}\\drone_battery", args=args, name="Drone Battery", skipEndIteration=True,
        )
        chargerUtilizationEstimator = ConstantEstimator(
            outputFolder=f"{folder}\\charger_utilization", args=args, name="Charger Capacity", skipEndIteration=True,
        )
        chargerFullEstimator = ConstantEstimator(
            outputFolder=f"{folder}\\charger_full", args=args, name="Charger Full", skipEndIteration=True,
        )
        droneStateEstimator = ConstantEstimator(
            outputFolder=f"{folder}\\drone_state", args=args, name="Drone State", skipEndIteration=True,
        )
        timeToChargingEstimator = ConstantEstimator(
            outputFolder=f"{folder}\\drone_time_to_charging", args=args, name="Time To Charging", skipEndIteration=True,
        )
        timeToLowBatteryEstimator = ConstantEstimator(
            outputFolder=f"{folder}\\drone_time_to_low_battery", args=args, name="Time To Low Battery", skipEndIteration=True,
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

    for estimator in WORLD.estimators:
        estimator.saveModel()

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
    # since we are using one map, we keep this argument optional with default value as map.yaml
    parser.add_argument('-i', '--input', type=str, help='YAML address to be run.',required=False,default="experiments\\map.yaml")
    # number of birds and drones are specified here, default is 1 (one),
    parser.add_argument('-b', '--birds', help='A range of birds [min,max]',required=False,nargs="+", default=[1])
    parser.add_argument('-x', '--drones', help='A range of drones [min,max]',required=False,nargs="+", default=[1])
    parser.add_argument('-f', '--folder', action='store_true', default=False, help='creates sub folders',required=False)
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
    parser.add_argument('-d', '--accumulate_data', action='store_true', default=False, help='False = use only training data from last iteration.\nTrue = accumulate training data from all previous iterations.')
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

    majorLog = Log([
        'Total Drones',
        'Total Birds',
        'Average Active Drones',
        'Average Total Damage',
        'Average Alive Drone Rate',
        'Average Damage Rate',
        'Train',
        'Average Run',
        'Charge Alert',
        'Battery Random Reduction'
    ])

    def createRange(iList):
        iList = [int(members) for members in iList]
        if len(iList) == 1:
            return range(iList[0],iList[0]+1)
        if len(iList) == 2:
            assert iList[1] > iList[0],"incorrect range"
            return range(iList[0],iList[1])
        if len(iList) == 3:
            assert iList[1] > iList[0],"incorrect range"
            return range(iList[0],iList[1],iList[2])
        return iList

    resultFolder = args.output
    for drones in createRange(args.drones):
        print (f"running with {drones} drones")
        for birds in createRange(args.birds):
            print (f"\trunning with {birds} birds")
            if args.folder:
                args.output = f"{resultFolder}\\d{drones}b{birds}"

            WORLD.estimators = []
            averageLog = run(args,drones,birds)
            newList = [drones,birds]
            newList.extend(averageLog.totalRecord())
            majorLog.register(newList)

    majorLog.exportNumeric(f"results\\{resultFolder}\\log.csv")


if __name__ == "__main__":
    main()