"""
Charger waiting time estimation
"""
import abc
import math

from common.components import DroneState, Drone, Charger
from common.estimator import *


class ChargerWaitingTimeEstimator(abc.ABC):

    @abc.abstractmethod
    def collectRecordStart(self, recordId, charger, drone, timeStep, **kwargs):
        pass

    @abc.abstractmethod
    def collectRecordEnd(self, recordId, timeStep):
        pass

    @abc.abstractmethod
    def predict(self, charger, drone):
        """
        Parameters
        ----------
        charger : Charger
        drone : Drone

        Returns
        -------
        float
        """
        return


###############
# Baseline: 0 #
###############


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


######################################
# Baseline: time to charge the queue #
######################################
# This estimate is obviously underestimating as it doesn't take into account energy consumed by the drones while they are waiting in the queue.


class QueueSumWaitingTimeEstimator(ChargerWaitingTimeEstimator, Estimator):

    def createDataCollector(self, inputs):
        return TimeDataCollector(inputs)

    def collectRecordStart(self, recordId, charger, drone, timeStep, **kwargs):
        self.dataCollector.collectRecordStart(recordId, {
            'queue_energy_required_sum': self.sumQueueEnergyRequired(charger),
            'charger_charging_capacity': self.chargerChargingCapacity(charger),

            # just for logging
            'queue_length': len(charger.chargingQueue),
            'charging_drones': len(charger.chargingDrones),
        }, timeStep, **kwargs)

    def collectRecordEnd(self, recordId, timeStep):
        self.dataCollector.collectRecordEnd(recordId, timeStep)

    @staticmethod
    def sumQueueEnergyRequired(charger):
        return sum([1 - d.battery for d in charger.chargingQueue + charger.chargingDrones])

    @staticmethod
    def chargerChargingCapacity(charger):
        return charger.chargingRate * charger.chargerCapacity

    def predict(self, charger, drone):
        return self.sumQueueEnergyRequired(charger) / self.chargerChargingCapacity(charger)


class QueueSumWaitingTimeEstimation(Estimation):

    def __init__(self, outputFolder):

        # these are not used to compute the estimates during simulation,
        # they are saved for evaluation
        estimationInputs = {
            'queue_energy_required_sum': NumberFeature(),
            'charger_charging_capacity': NumberFeature(),

            # just for logging
            'queue_length': NumberFeature(),
            'charging_drones': NumberFeature(),
        }

        super().__init__(estimationInputs, outputFolder)

    def _createEstimator(self, inputs):
        return QueueSumWaitingTimeEstimator(self, inputs)

    def _evaluate_predict(self, x):
        # same computation as QueueSumWaitingTimeEstimator.predict
        return (x[:, 0] / x[:, 1]).reshape((-1, 1))


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
    elif estimationType == "queue_energy_sum":
        return QueueSumWaitingTimeEstimation(outputFolder)
    else:
        raise NotImplementedError(f"Estimation '{estimationType}' not implemented.")
