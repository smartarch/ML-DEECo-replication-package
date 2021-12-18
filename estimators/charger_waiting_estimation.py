"""
Charger waiting time estimation
"""
import math

from simulation.charger import Charger
from simulation.drone import DroneState
from estimators.estimator import *

# CURRENTLY UNUSED

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
        }, timeStep, **kwargs)

    def collectRecordEnd(self, recordId, timeStep):
        self.dataCollector.collectRecordEnd(recordId, timeStep)

    @staticmethod
    def sumQueueMissingBattery(charger):
        return sum([1 - d.battery for d in charger.waitingDrones + charger.chargingDrones])

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
        }, timeStep, **kwargs)

    def collectRecordEnd(self, recordId, timeStep):
        self.dataCollector.collectRecordEnd(recordId, timeStep)

    @staticmethod
    def computeQueueChargingTime(charger: Charger, energyConsumptionRate: float, untilAcceptance=True):
        """
        Parameters
        ----------
        charger
        energyConsumptionRate
        untilAcceptance : bool
            If ``True``, compute time until there is at least one free spot in ``charger.acceptedDrones``, i.e. the new drone will be accepted.
            If ``False``, compute time to charge the whole queue.
        """
        queue = [d.battery for d in charger.acceptedDrones]
        charging = [d.battery for d in charger.chargingDrones]
        chargingRate = charger.chargingRate

        # if there are free slots, move the drones from the queue (assume they start charging immediately)
        freeSlots = charger.chargerCapacity - len(charging)
        charging.extend(queue[:freeSlots])
        del queue[:freeSlots]

        # compute the charging time
        chargingTime = 0

        while len(charging) > 0:
            if untilAcceptance and len(queue) < charger.acceptedCapacity:  # there is a free spot in the acceptedDrones
                break

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
            'potential_drones_length': len(charger.potentialDrones),
            'accepted_drones_length': len(charger.acceptedDrones),
            'accepted_drones_battery': sum([drone.battery for drone in charger.acceptedDrones]),
            'charging_drones_length': len(charger.chargingDrones),
            'charging_drones_battery': sum([drone.battery for drone in charger.chargingDrones]),
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
            'potential_drones_length': FloatFeature(0, len(world.drones)),
            'accepted_drones_length': FloatFeature(0, world.chargerCapacity),
            'accepted_drones_battery': FloatFeature(0, world.chargerCapacity),
            'charging_drones_length': FloatFeature(0, world.chargerCapacity),
            'charging_drones_battery': FloatFeature(0, world.chargerCapacity),
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