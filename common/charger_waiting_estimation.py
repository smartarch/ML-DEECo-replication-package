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

    def predictBatch(self, charger, drones):
        """
        Parameters
        ----------
        charger : Charger
        drones : list[Drone]
            The batch of drones: batch_size = len(drones)

        Returns
        -------
        np.ndarray
            Shape [batch_size]
        """
        return np.array([self.predict(charger, drone) for drone in drones])


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

    def __init__(self, **kwargs):
        super().__init__({}, **kwargs)

    def _createEstimator(self, inputs):
        return BaselineZeroChargerWaitingTimeEstimator(self, inputs)


####################################################
# Baseline: missing battery of drones in the queue #
####################################################
# This estimate is obviously underestimating as it doesn't take into account energy consumed by the drones while they are waiting in the queue.


class QueueMissingBatteryWaitingTimeEstimator(ChargerWaitingTimeEstimator, Estimator):

    def createDataCollector(self, inputs):
        return TimeDataCollector(inputs)

    def collectRecordStart(self, recordId, charger, drone, timeStep, **kwargs):
        self.dataCollector.collectRecordStart(recordId, {
            'queue_missing_battery_sum': self.sumQueueMissingBattery(charger),
            'charger_charging_capacity': self.chargerChargingCapacity(charger),

            # just for logging
            'queue_length': len(charger.chargingQueue),
            'charging_drones': len(charger.chargingDrones),
        }, timeStep, **kwargs)

    def collectRecordEnd(self, recordId, timeStep):
        self.dataCollector.collectRecordEnd(recordId, timeStep)

    @staticmethod
    def sumQueueMissingBattery(charger):
        return sum([1 - d.battery for d in charger.chargingQueue + charger.chargingDrones])

    @staticmethod
    def chargerChargingCapacity(charger):
        return charger.chargingRate * charger.chargerCapacity

    def predict(self, charger, drone):
        return self.sumQueueMissingBattery(charger) / self.chargerChargingCapacity(charger)


class QueueMissingBatteryWaitingTimeEstimation(Estimation):

    @property
    def name(self):
        return "Queue missing battery"

    def __init__(self, **kwargs):

        # these are not used to compute the estimates during simulation,
        # they are saved for evaluation
        estimationInputs = {
            'queue_missing_battery_sum': NumberFeature(),
            'charger_charging_capacity': NumberFeature(),

            # just for logging
            'queue_length': NumberFeature(),
            'charging_drones': NumberFeature(),
        }

        super().__init__(estimationInputs, **kwargs)

    def _createEstimator(self, inputs):
        return QueueMissingBatteryWaitingTimeEstimator(self, inputs)

    def _evaluate_predict(self, x):
        # same computation as QueueSumWaitingTimeEstimator.predict
        return (x[:, 0] / x[:, 1]).reshape((-1, 1))


########################################
# Baseline: charging time of the queue #
########################################
# This includes an estimate of the energy consumed by the drones while waiting in the queue (assuming the Drone.droneMovingEnergyConsumption).


class QueueChargingTimeWaitingTimeEstimator(ChargerWaitingTimeEstimator, Estimator):

    def createDataCollector(self, inputs):
        return TimeDataCollector(inputs)

    def collectRecordStart(self, recordId, charger, drone, timeStep, **kwargs):
        self.dataCollector.collectRecordStart(recordId, {
            'queue_charging_time': self.computeQueueChargingTime(charger, drone.droneMovingEnergyConsumption),

            # just for logging
            'queue_missing_battery_sum': QueueMissingBatteryWaitingTimeEstimator.sumQueueMissingBattery(charger),
            'charger_charging_capacity': QueueMissingBatteryWaitingTimeEstimator.chargerChargingCapacity(charger),
            'queue_length': len(charger.chargingQueue),
            'charging_drones': len(charger.chargingDrones),
        }, timeStep, **kwargs)

    def collectRecordEnd(self, recordId, timeStep):
        self.dataCollector.collectRecordEnd(recordId, timeStep)

    @staticmethod
    def computeQueueChargingTime(charger: Charger, energyConsumptionRate: float):
        queue = [d.battery for d in charger.chargingQueue]
        charging = [d.battery for d in charger.chargingDrones]
        chargingRate = charger.chargingRate

        # if there are free slots, move the drones from the queue
        freeSlots = charger.chargerCapacity - len(charging)
        charging.extend(queue[:freeSlots])
        del queue[:freeSlots]

        # compute the charging time
        chargingTime = 0

        while len(charging) > 0:
            maxBattery = max(charging)
            timeUntilCharged = (1 - maxBattery) / chargingRate
            chargingTime += timeUntilCharged

            queue = [bat - energyConsumptionRate * chargingTime for bat in queue]
            queue = [bat for bat in queue if bat > 0]

            charging.remove(maxBattery)
            if len(queue) > 0:
                charging.append(queue[0])
                del queue[0]

        return chargingTime

    def predict(self, charger, drone):
        return self.computeQueueChargingTime(charger, drone.droneMovingEnergyConsumption)


class QueueChargingTimeWaitingTimeEstimation(Estimation):

    @property
    def name(self):
        return "Queue charging time"

    def __init__(self, **kwargs):

        # these are not used to compute the estimates during simulation,
        # they are saved for evaluation
        estimationInputs = {
            'queue_charging_time': NumberFeature(),

            # just for logging
            'queue_missing_battery_sum': NumberFeature(),
            'charger_charging_capacity': NumberFeature(),
            'queue_length': NumberFeature(),
            'charging_drones': NumberFeature(),
        }

        super().__init__(estimationInputs, **kwargs)

    def _createEstimator(self, inputs):
        return QueueChargingTimeWaitingTimeEstimator(self, inputs)

    def _evaluate_predict(self, x):
        # use the value computed at the time of saving the datum
        return x[:, 0].reshape((-1, 1))


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

    def predictBatch(self, charger, drones):
        return NeuralNetworkTimeEstimator.predictBatch(self, [self.generateFeatures(charger, d) for d in drones])


class NeuralNetworkChargerWaitingTimeEstimation(NeuralNetworkTimeEstimation):

    def __init__(self, hidden_layers, world, **kwargs):

        estimationInputs = {
            'drone_battery': FloatFeature(0, 1),
            'drone_state': IntEnumFeature(DroneState),
            'charger_distance': FloatFeature(0, math.sqrt(world.mapWidth ** 2 + world.mapHeight ** 2)),
            'queue_length': FloatFeature(0, len(world.drones) / world.chargerCapacity),
            # number of drones in the waiting queue divided by the number of drones which can be charged simultaneously
            'charging_drones': FloatFeature(0, world.chargerCapacity),  # number of drones currently being charged
        }

        super().__init__(estimationInputs, hidden_layers, **kwargs)

    def _createEstimator(self, inputs):
        return NeuralNetworkChargerWaitingTimeEstimator(self, inputs)


########################
# Estimation selection #
########################


def getChargerWaitingTimeEstimation(world, args, outputFolder):

    estimationType = args.waiting_estimation
    kwargs = {
        'outputFolder': outputFolder,
        'args': args,
    }

    if estimationType == "baseline_zero":
        return BaselineZeroChargerWaitingTimeEstimation(**kwargs)
    elif estimationType == "neural_network":
        return NeuralNetworkChargerWaitingTimeEstimation(args.hidden_layers, world, **kwargs)
    elif estimationType == "queue_missing_battery":
        return QueueMissingBatteryWaitingTimeEstimation(**kwargs)
    elif estimationType == "queue_charging_time":
        return QueueChargingTimeWaitingTimeEstimation(**kwargs)
    else:
        raise NotImplementedError(f"Estimation '{estimationType}' not implemented.")
