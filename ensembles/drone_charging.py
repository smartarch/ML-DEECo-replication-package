"""
Drone charging ensembles
"""
import math
from typing import List

from estimators.features import FloatFeature
from simulation.drone import DroneState
from simulation.ensemble import Ensemble, someOf
from utils.verbose import verbosePrint


def getEnsembles(WORLD, estimation):

    Drone = WORLD.Drone
    Charger = WORLD.Charger

    class PotentialDronesAssignment(Ensemble):

        charger: Charger

        def __init__(self, charger):
            self.charger = charger

        def priority(self):
            return 2  # It is necessary to run this before AcceptedDronesAssignment. The order of PotentialDronesAssignment ensembles can be arbitrary as they don't influence each other.

        drones: List[Drone] = someOf(Drone)

        @drones.cardinality
        def drones(self):
            return 0, len(self.charger.world.drones)

        @drones.select
        def drones(self, drone, otherEnsembles):
            return drone.state not in (DroneState.TERMINATED, DroneState.MOVING_TO_CHARGER, DroneState.CHARGING) and \
                   drone.findClosestCharger() == self.charger

        def actuate(self):
            self.charger.potentialDrones = self.drones
            for drone in self.drones:
                drone.closestCharger = self.charger

            verbosePrint(f"Charger Finder: assigned {len(self.drones)} to {self.charger.id}", 4)

    class AcceptedDronesAssignment(Ensemble):

        charger: Charger

        def __init__(self, charger):
            self.charger = charger

        def priority(self):
            return 1  # The order of AcceptedDronesAssignment ensembles can be arbitrary as they don't influence each other.

        drones: List[Drone] = someOf(Drone).withSelectionTimeEstimate(estimation)

        @drones.cardinality
        def drones(self):
            return 0, self.charger.acceptedCapacity

        @drones.select
        def drones(self, drone, otherEnsembles):
            if drone.state == DroneState.TERMINATED:
                return False

            waitingTimeEstimate = self.drones.selectionTimeEstimate.estimate(self, drone)
            timeToFlyToCharger = drone.timeToFlyToCharger()

            # was accepted before or needs charging
            cond = drone in self.charger.acceptedDrones or \
                   drone in self.charger.potentialDrones and \
                   drone.needsCharging(waitingTimeEstimate + timeToFlyToCharger)

            cond = cond and self.charger.timeToDoneCharging() <= drone.timeToFlyToCharger()

            return cond

        @drones.priority
        def drones(self, drone):
            if drone in self.charger.acceptedDrones:
                return 1  # keep the accepted drones from previous time steps  # TODO: think about this later
            return -drone.timeToDoneCharging()

        @drones.selectionTimeEstimate.input(FloatFeature(0, 1))
        def battery(self, drone):
            return drone.battery

        @drones.selectionTimeEstimate.input(FloatFeature(0, math.sqrt(WORLD.mapWidth ** 2 + WORLD.mapHeight ** 2)))
        def charger_distance(self, drone):
            return self.charger.location.distance(drone.location)

        # TODO(MT): more features

        # @drones.selectionTimeEstimate.id
        # def id(self, drone):
        #     return drone.id

        @drones.selectionTimeEstimate.filter
        def filter(self, drone):
            return drone not in self.charger.acceptedDrones  # don't collect the data if the drone was already selected in the previous step

        @drones.selectionTimeEstimate.time
        def time(self, drone):
            return WORLD.currentTimeStep

        def actuate(self):

            verbosePrint(f"Charging Ensemble: assigned {len(self.drones)} to {self.charger.id}", 4)

            # for drone in self.drones:
            #     if drone in self.charger.acceptedDrones:
            #         continue
            #     # TODO(MT): move the estimator to the ensemble
            #     self.charger.waitingTimeEstimator.collectRecordEnd(drone.id, WORLD.currentTimeStep)
            #     self.charger.world.chargerLog.register([
            #         drone.world.currentTimeStep,
            #         drone.id,
            #         drone.battery,
            #         drone.computeFutureBattery(),
            #         drone.estimateWaitingEnergy(drone.closestCharger),
            #         drone.energyToFlyToCharger(),
            #         drone.timeToDoneCharging(),
            #         self.charger.id,
            #         len(self.charger.potentialDrones),
            #         len(self.charger.acceptedDrones),
            #         len(self.charger.chargingDrones),
            #     ])

            self.charger.acceptedDrones = self.drones

    ensembles = \
        [PotentialDronesAssignment(charger) for charger in WORLD.chargers] + \
        [AcceptedDronesAssignment(charger) for charger in WORLD.chargers]

    return ensembles
