"""
Charger waiting time estimation
"""
import abc
import math

from common.components import DroneState
from common.estimator import BaselineTimeEstimator, BaselineEstimation, NeuralNetworkTimeEstimation, NeuralNetworkTimeEstimator, FloatFeature, IntEnumFeature


class ChargerWaitingTimeEstimator(abc.ABC):

    @abc.abstractmethod
    def collectRecordStart(self, recordId, charger, drone, timeStep, **kwargs):
        pass

    @abc.abstractmethod
    def collectRecordEnd(self, recordId, timeStep):
        pass

    @abc.abstractmethod
    def predict(self, charger, drone):
        return


##############
# Baseline 0 #
##############


class BaselineZeroChargerWaitingTimeEstimator(ChargerWaitingTimeEstimator, BaselineTimeEstimator):

    def collectRecordStart(self, recordId, charger, drone, timeStep, **kwargs):
        self.dataCollector.collectRecordStart(recordId, None, timeStep, **kwargs)

    def collectRecordEnd(self, recordId, timeStep):
        self.dataCollector.collectRecordEnd(recordId, timeStep)

    def predict(self, charger, drone):
        return BaselineTimeEstimator.predict(self, None)


class BaselineZeroChargerWaitingTimeEstimation(BaselineEstimation):

    def __init__(self, outputFolder):
        super().__init__({}, outputFolder)

    def _createEstimator(self, inputs):
        return BaselineZeroChargerWaitingTimeEstimator(self, inputs)


##################
# Neural network #
##################


class NeuralNetworkChargerWaitingTimeEstimator(ChargerWaitingTimeEstimator, NeuralNetworkTimeEstimator):

    @staticmethod
    def generateFeatures(charger, drone):
        return {
            'drone_battery': drone.battery,
            'drone_state': int(drone.state),
            'charger_distance': charger.location.distance(drone.location),
            'queue_length': len(charger.chargingQueue) / charger.chargerCapacity,
            'charging_drones': len(charger.chargingDrones),
        }

    def collectRecordStart(self, recordId, charger, drone, timeStep, **kwargs):
        self.dataCollector.collectRecordStart(recordId, self.generateFeatures(charger, drone), timeStep, **kwargs)

    def collectRecordEnd(self, recordId, timeStep):
        self.dataCollector.collectRecordEnd(recordId, timeStep)

    def predict(self, charger, drone):
        return NeuralNetworkTimeEstimator.predict(self, self.generateFeatures(charger, drone))


class NeuralNetworkChargerWaitingTimeEstimation(NeuralNetworkTimeEstimation):

    def __init__(self, outputFolder, hidden_layers, world):

        estimationInputs = {
            'drone_battery': FloatFeature(0, 1),
            'drone_state': IntEnumFeature(DroneState),
            'charger_distance': FloatFeature(0, math.sqrt(world.mapWidth ** 2 + world.mapHeight ** 2)),
            'queue_length': FloatFeature(0, len(world.drones) / world.chargerCapacity),
            # number of drones in the waiting queue divided by the number of drones which can be charged simultaneously
            'charging_drones': FloatFeature(0, world.chargerCapacity),  # number of drones currently being charged
        }

        super().__init__(estimationInputs, outputFolder, hidden_layers)

    def _createEstimator(self, inputs):
        return NeuralNetworkChargerWaitingTimeEstimator(self, inputs)


########################
# Estimation selection #
########################


def getChargerWaitingTimeEstimation(world, args, outputFolder):

    estimationType = args.waiting_estimation

    if estimationType == "baseline_zero":
        return BaselineZeroChargerWaitingTimeEstimation(outputFolder)
    elif estimationType == "neural_network":
        return NeuralNetworkChargerWaitingTimeEstimation(outputFolder, args.hidden_layers, world)
    else:
        raise NotImplementedError(f"Estimation '{estimationType}' not implemented.")
