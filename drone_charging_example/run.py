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

from world import WORLD, ENVIRONMENT  # This import should be first
from components.drone_state import DroneState
from utils.visualizers import Visualizer
from utils import plots

from ml_deeco.estimators import ConstantEstimator, NeuralNetworkEstimator, NoEstimator
from ml_deeco.simulation import run_simulation, SIMULATION_GLOBALS
from ml_deeco.utils import setVerboseLevel, verbosePrint, Log


def run(args):
    # Fix random seeds
    random.seed(args.seed)
    np.random.seed(args.seed)
    tf.random.set_seed(args.seed)

    # Set number of threads
    tf.config.threading.set_inter_op_parallelism_threads(args.threads)
    tf.config.threading.set_intra_op_parallelism_threads(args.threads)

    yamlObject = loadConfig(args)

    folder, yamlFileName = prepareFoldersForResults(args)
    estWaitingFolder = f"{folder}\\{args.waiting_estimation}"

    averageLog, totalLog = createLogs()

    waitingTimeEstimator = createEstimators(args, folder, estWaitingFolder)

    # start the main loop
    for t in range(args.train):
        verbosePrint(f"Iteration {t + 1} started at {datetime.now()}:", 1)

        for i in range(args.number):

            components, ensembles = WORLD.reset()
            if args.animation:
                visualizer = Visualizer(WORLD)
                visualizer.drawFields()

            def stepCallback(components, materializedEnsembles, iteration):
                # Collect statistics
                for chargerIndex in range(len(WORLD.chargers)):
                    charger = WORLD.chargers[chargerIndex]
                    accepted = set(charger.acceptedDrones)
                    waiting = set(charger.waitingDrones)
                    potential = set(charger.potentialDrones)
                    WORLD.chargerLogs[chargerIndex].register([
                        # sum([drone.battery for drone in charger.potentialDrones])/potentialDrones,
                        len(charger.chargingDrones),
                        len(accepted),
                        len(waiting - accepted),
                        len(potential - waiting - accepted),
                    ])

                if args.animation:
                    visualizer.drawComponents(i + 1)

            verbosePrint(f"Run {i + 1} started at {datetime.now()}:", 2)
            run_simulation(components, ensembles, ENVIRONMENT.maxSteps, stepCallback)

            totalLog.register(collectStatistics(t, i))
            WORLD.chargerLog.export(f"{folder}/charger_logs/{yamlFileName}_{t + 1}_{i + 1}.csv")

            if args.animation:
                verbosePrint(f"Saving animation...", 3)
                visualizer.createAnimation(f"{folder}/animations/{yamlFileName}_{t + 1}_{i + 1}.gif")
                verbosePrint(f"Animation saved.", 3)

            if args.chart:
                verbosePrint(f"Saving charger plot...", 3)
                plots.createChargerPlot(
                    WORLD.chargerLogs,
                    f"{folder}\\charger_logs\\{yamlFileName}_{str(t + 1)}_{str(i + 1)}",
                    f"World: {yamlFileName}\nEstimator: {waitingTimeEstimator.estimatorName}\n Run: {i + 1} in training {t + 1}\nCharger Queues")
                verbosePrint(f"Charger plot saved.", 3)

        # calculate the average rate
        if t > 0:
            averageLog.register(totalLog.average(t * args.number, (t + 1) * args.number))

        for estimator in SIMULATION_GLOBALS.estimators:
            estimator.endIteration()
            estimator.saveModel(t + 1)

    totalLog.export(f"{folder}\\{yamlFileName}_{args.waiting_estimation}.csv")
    if args.train > 1:
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


def loadConfig(args):
    # load config from yaml
    yamlFile = open(args.input, 'r')
    yamlObject = load(yamlFile, Loader=Loader)

    # yamlObject['drones']=drones
    # yamlObject['birds']=birds
    # yamlObject['maxSteps']=int(args.timesteps)
    yamlObject['chargerCapacity'] = findChargerCapacity(yamlObject)
    yamlObject['totalAvailableChargingEnergy'] = min(
        yamlObject['chargerCapacity'] * len(yamlObject['chargers']) * yamlObject['chargingRate'],
        yamlObject['totalAvailableChargingEnergy'])

    ENVIRONMENT.loadConfig(yamlObject)
    # print (f"chargerCapacity: {yamlObject['chargerCapacity']}")
    # print( f"totalAvailableChargingEnergy: {yamlObject['totalAvailableChargingEnergy']}")

    return yamlObject


def findChargerCapacity(yamlObject):
    margin = 1.3
    chargers = len(yamlObject['chargers'])
    drones = yamlObject['drones']

    c1 = yamlObject['chargingRate']
    c2 = yamlObject['droneMovingEnergyConsumption']

    return math.ceil(
        (margin * drones * c2) / ((chargers * c1) + (chargers * margin * c2))
    )


def createLogs():
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
    return averageLog, totalLog


def prepareFoldersForResults(args):
    # prepare folder structure for results
    yamlFileName = os.path.splitext(os.path.basename(args.input))[0]
    folder = f"results\\{args.output}"

    if not os.path.exists(f"{folder}\\animations"):
        os.makedirs(f"{folder}\\animations")
    if not os.path.exists(f"{folder}\\charger_logs"):
        os.makedirs(f"{folder}\\charger_logs")
    return folder, yamlFileName


def createEstimators(args, folder, estWaitingFolder):
    # create the estimators
    commonArgs = {
        "accumulateData": args.accumulate_data,
        "saveCharts": args.chart,
        "testSplit": args.test_split,
    }
    waitingTimeEstimatorArgs = {
        "outputFolder": estWaitingFolder,
        "name": "Waiting Time",
    }
    if args.waiting_estimation == "baseline":
        waitingTimeEstimator = ConstantEstimator(args.baseline, **waitingTimeEstimatorArgs, **commonArgs)
    else:
        waitingTimeEstimator = NeuralNetworkEstimator(
            args.hidden_layers,
            fit_params={
                "batch_size": 256,
            },
            **waitingTimeEstimatorArgs,
            **commonArgs,
        )
    if args.examples:
        fit_params = {
            "epochs": 20,
        }
        droneBatteryEstimator = NeuralNetworkEstimator(
            hidden_layers=[32, 32], fit_params=fit_params,
            **commonArgs,
            outputFolder=f"{folder}\\drone_battery", name="Drone Battery"
        )
        chargerUtilizationEstimator = NeuralNetworkEstimator(
            hidden_layers=[32, 32], fit_params=fit_params,
            **commonArgs,
            outputFolder=f"{folder}\\charger_utilization", name="Charger Capacity"
        )
        chargerFullEstimator = NeuralNetworkEstimator(
            hidden_layers=[32, 32], fit_params=fit_params,
            **commonArgs,
            outputFolder=f"{folder}\\charger_full", name="Charger Full"
        )
        droneStateEstimator = NeuralNetworkEstimator(
            hidden_layers=[32, 32], fit_params=fit_params,
            **commonArgs,
            outputFolder=f"{folder}\\drone_state", name="Drone State"
        )
        timeToChargingEstimator = NeuralNetworkEstimator(
            hidden_layers=[32, 32], fit_params=fit_params,
            **commonArgs,
            outputFolder=f"{folder}\\drone_time_to_charging", name="Time To Charging"
        )
        timeToLowBatteryEstimator = NeuralNetworkEstimator(
            hidden_layers=[32, 32], fit_params=fit_params,
            **commonArgs,
            outputFolder=f"{folder}\\drone_time_to_low_battery", name="Time To Low Battery"
        )
    else:
        droneBatteryEstimator = NoEstimator(
            **commonArgs, name="Drone Battery"
        )
        chargerUtilizationEstimator = NoEstimator(
            **commonArgs, name="Charger Capacity"
        )
        chargerFullEstimator = NoEstimator(
            **commonArgs, name="Charger Full"
        )
        droneStateEstimator = NoEstimator(
            **commonArgs, name="Drone State"
        )
        timeToChargingEstimator = NoEstimator(
            **commonArgs, name="Time To Charging"
        )
        timeToLowBatteryEstimator = NoEstimator(
            **commonArgs, name="Time To Low Battery"
        )
    WORLD.waitingTimeEstimator = waitingTimeEstimator
    WORLD.droneBatteryEstimator = droneBatteryEstimator
    WORLD.chargerUtilizationEstimator = chargerUtilizationEstimator
    WORLD.chargerFullEstimator = chargerFullEstimator
    WORLD.droneStateEstimator = droneStateEstimator
    WORLD.timeToChargingEstimator = timeToChargingEstimator
    WORLD.timeToLowBatteryEstimator = timeToLowBatteryEstimator
    return waitingTimeEstimator


def collectStatistics(train, iteration):
    MAXDRONES = ENVIRONMENT.droneCount if ENVIRONMENT.droneCount > 0 else 1
    MAXDAMAGE = sum([field.allCrops for field in WORLD.fields])

    return [
        len([drone for drone in WORLD.drones if drone.state != DroneState.TERMINATED]),
        sum([field.damage for field in WORLD.fields]),
        len([drone for drone in WORLD.drones if drone.state != DroneState.TERMINATED]) / MAXDRONES,  # rate
        sum([field.damage for field in WORLD.fields]) / MAXDAMAGE,  # rage
        ENVIRONMENT.chargerCapacity,
        train + 1,
        iteration + 1,
        0.2,
        ENVIRONMENT.droneBatteryRandomize,
    ]


def main():
    parser = argparse.ArgumentParser(description='Process YAML source file (S) and run the simulation (N) Times with Model M.')
    # since we are using one map, we keep this argument optional with default value as map.yaml
    parser.add_argument('input', type=str, help='YAML address to be run.')
    # number of birds and drones are specified here, default is 1 (one),
    # parser.add_argument('-b', '--birds', help='A range of birds [min,max]',required=False,nargs="+", default=[1])
    # parser.add_argument('-x', '--drones', help='A range of drones [min,max]',required=False,nargs="+", default=[1])
    # parser.add_argument('-m', '--timesteps', help='Maximum timesteps',required=False,default=500)
    # parser.add_argument('-f', '--folder', action='store_true', default=False, help='creates sub folders',required=False)
    parser.add_argument('-n', '--number', type=int, help='the number of simulation runs per training.', required=False, default="1")
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
    # parser.add_argument('-q', '--queue_type', type=str, choices=["fifo", "priority"], help='Charging waiting queue.', required=False,
    #                     default="fifo")
    parser.add_argument('-d', '--accumulate_data', action='store_true', default=False,
                        help='False = use only training data from last iteration.\nTrue = accumulate training data from all previous iterations.')
    parser.add_argument('--test_split', type=float, help='Number of records used for evaluation.', required=False, default=0.2)
    parser.add_argument('--hidden_layers', nargs="+", type=int, default=[256, 256], help='Number of neurons in hidden layers.')
    parser.add_argument('-s', '--seed', type=int, help='Random seed.', required=False, default=42)
    parser.add_argument('-b', '--baseline', type=int, help='Constant for baseline.', required=False, default=0)
    parser.add_argument('-e', '--examples', action='store_true', default=False, help='Additional examples.')
    parser.add_argument('--threads', type=int, help='Number of CPU threads TF can use.', required=False, default=4)
    args = parser.parse_args()

    number = args.number
    setVerboseLevel(args.verbose)

    if number <= 0:
        raise argparse.ArgumentTypeError(f"{number} is an invalid positive int value")

    run(args)

    # majorLog = Log([
    #     'Estimator',
    #     'Drones',
    #     'Bird',
    #     'Active Drones',
    #     'Total Damage',
    #     'Alive Drone Rate',
    #     'Damage Rate',
    #     'Charger Capacity',
    #     'Train',
    #     'Average Run',
    #     'Charge Alert',
    #     'Battery Random Reduction'
    # ])

    # def createRange(iList):
    #     iList = [int(members) for members in iList]
    #     if len(iList) == 1:
    #         return range(iList[0],iList[0]+1)
    #     if len(iList) == 2:
    #         assert iList[1] > iList[0],"incorrect range"
    #         return range(iList[0],iList[1])
    #     if len(iList) == 3:
    #         assert iList[1] > iList[0],"incorrect range"
    #         return range(iList[0],iList[1],iList[2])
    #     return iList

    # resultFolder = args.output
    # for drones in createRange(args.drones):
    #     print (f"running with {drones} drones")
    #     for birds in createRange(args.birds):
    #         print (f"\trunning with {birds} birds")
    #         if args.folder:
    #             args.output = f"{resultFolder}\\birds-{birds}"
    #         averageLog = run(args,drones,birds)
    #         topRow = [
    #             'no estimator',
    #             drones,
    #             birds]
    #         topRow.extend(averageLog.records[1])
    #         secondRow = [
    #             f'{args.train} trains',
    #             drones,
    #             birds]
    #         secondRow.extend(averageLog.totalRecord())
    #         majorLog.register(topRow)
    #         majorLog.register(secondRow)

    # majorLog.export(f"results\\{resultFolder}\\log.csv")
    # path = os.path.realpath(f"results\\{resultFolder}")
    # os.startfile(path)


if __name__ == "__main__":
    main()
