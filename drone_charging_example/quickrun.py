# TODO: do we use this?
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

from drone_charging_example.world import WORLD, ENVIRONMENT  # This import should be first
from ml_deeco.estimators.estimator import ConstantEstimator, NeuralNetworkEstimator
from ml_deeco.simulation.simulation import Simulation
from drone_charging_example.utls import plots
from ml_deeco.utils.serialization import Log
from ml_deeco.utils.verbose import setVerboseLevel, verbosePrint


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

    if not os.path.exists(f"{folder}\\animations"):
        os.makedirs(f"{folder}\\animations")

    if not os.path.exists(f"{folder}\\charger_logs"):
        os.makedirs(f"{folder}\\charger_logs")

    totalLog = Log([
        'Active Drones',
        'Total Damage',
        'Alive Drone Rate',
        'Damage Rate',
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
            activation=tf.keras.activations.sigmoid,  # We want a value between 0 and 1
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
            outputFolder=f"{folder}\\drone_battery", args=args, name="Drone Battery"
        )
        chargerUtilizationEstimator = ConstantEstimator(
            outputFolder=f"{folder}\\charger_utilization", args=args, name="Charger Capacity"
        )
        chargerFullEstimator = ConstantEstimator(
            outputFolder=f"{folder}\\charger_full", args=args, name="Charger Full"
        )
        droneStateEstimator = ConstantEstimator(
            outputFolder=f"{folder}\\drone_state", args=args, name="Drone State"
        )
        timeToChargingEstimator = ConstantEstimator(
            outputFolder=f"{folder}\\drone_time_to_charging", args=args, name="Time To Charging"
        )
        timeToLowBatteryEstimator = ConstantEstimator(
            outputFolder=f"{folder}\\drone_time_to_low_battery", args=args, name="Time To Low Battery"
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
            newLog, chargerLogs = simulation.quickrun(yamlFileName,t,i, args)

            if args.chart:
                verbosePrint(f"Saving charger plot...", 3)
                plots.createChargerPlot(
                    chargerLogs,
                    f"{folder}\\charger_logs\\{yamlFileName}_{str(t + 1)}_{str(i + 1)}",
                    f"World: {yamlFileName}\nEstimator: {waitingTimeEstimator.estimatorName}\n Run: {i + 1} in training {t + 1}\nCharger Queues")
                verbosePrint(f"Charger plot saved.", 3)
            totalLog.register(newLog)
        # calculate the average rate
        averageLog.register(totalLog.average(t*args.number,(t+1)*args.number))
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

    run(args)


if __name__ == "__main__":
    main()


# def collectRates(self, previousRates):
#     if previousRates is None:
#         previousRates ={
#             'Damage':0,
#             'Energy':0,
#         }
#     return [
#         WORLD.currentTimeStep,
#         WORLD.drones[0].alert,
#         ENVIRONMENT.droneBatteryRandomize,
#         len([drone for drone in WORLD.drones if drone.state != DroneState.TERMINATED]),
#         len([drone for drone in WORLD.drones if drone.state != DroneState.TERMINATED])/self.MAXDRONES,
#         sum([bird.ate for bird in WORLD.birds])-previousRates['Damage'],
#         sum([bird.ate for bird in WORLD.birds]),
#         sum([charger.energyConsumed for charger in WORLD.chargers])-previousRates['Energy'],
#         sum([charger.energyConsumed for charger in WORLD.chargers])
#     ]
#
#
# def quickrun(self, filename, train, iteration, args):
#     log = Log([
#         'Iterations',
#         'Charge Alert',
#         'Battery Randomize',
#         'Alive Drones',
#         'Drone Live Rate',
#         'Damage',
#         'Cumulative Damage',
#         'Consumed Energy',
#         'Cumulative Consumed Energy'
#     ])
#     components = []
#
#     components.extend(WORLD.drones)
#
#     components.extend(WORLD.birds)
#     components.extend(WORLD.chargers)
#
#     from drone_charging_example.ensembles.field_protection import getEnsembles as fieldProtectionEnsembles
#     from drone_charging_example.ensembles.drone_charging import getEnsembles as droneChargingEnsembles
#     potentialEnsembles = fieldProtectionEnsembles() + droneChargingEnsembles()
#
#     WORLD.initEstimators()
#
#     if self.visualize:
#         visualizer = Visualizer(WORLD)
#         visualizer.drawFields()
#     previousRates = None
#     for i in range(ENVIRONMENT.maxSteps):
#         verbosePrint(f"Step {i + 1}:", 3)
#         WORLD.currentTimeStep = i
#
#         # Ensembles
#         initializedEnsembles = []
#
#         potentialEnsembles = sorted(potentialEnsembles)
#
#         for ens in potentialEnsembles:
#             if ens.materialize(components, initializedEnsembles):
#                 initializedEnsembles.append(ens)
#                 ens.actuate()
#
#         # Components
#         for component in components:
#             component.actuate()
#             component.collectEstimatesData()
#             verbosePrint(f"{component}", 4)
#
#         if i % 50 == 0:
#             rate = self.collectRates(previousRates)
#             previousRates = {
#                 'Damage': rate[5],
#                 'Energy': rate[7]
#             }
#             log.register(rate)
#
#         # # Collect statistics
#         # for chargerIndex in range(len(self.world.chargers)):
#         #     charger = self.world.chargers[chargerIndex]
#         #     accepted = set(charger.acceptedDrones)
#         #     waiting = set(charger.waitingDrones)
#         #     potential = set(charger.potentialDrones)
#         #     self.world.chargerLogs[chargerIndex].register([
#         #         # sum([drone.battery for drone in charger.potentialDrones])/potentialDrones,
#         #         len(charger.chargingDrones),
#         #         len(accepted),
#         #         len(waiting - accepted),
#         #         len(potential - waiting - accepted),
#         #     ])
#
#         if self.visualize:
#             visualizer.drawComponents(i + 1)
#
#     if self.visualize:
#         verbosePrint(f"Saving animation...", 3)
#         visualizer.createAnimation(f"{self.folder}/animations/{filename}_{train + 1}_{iteration + 1}.gif")
#         verbosePrint(f"Animation saved.", 3)
#
#     WORLD.chargerLog.export(f"{self.folder}/charger_logs/{filename}_{train + 1}_{iteration + 1}.csv")
#
#     WORLD.currentTimeStep = ENVIRONMENT.maxSteps
#     log.register(self.collectRates(previousRates))
#     log.export(f"{self.folder}/{filename}_{train + 1}_{iteration + 1}.csv")
#     return self.collectStatistics(train, iteration), WORLD.chargerLogs
