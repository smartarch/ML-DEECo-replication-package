"""
Drone charging ensembles
"""
import math
from typing import List, TYPE_CHECKING

from simulation.world import ENVIRONMENT, WORLD
from estimators.features import FloatFeature, IntEnumFeature
from simulation.ensemble import Ensemble, someOf
from simulation.drone_state import DroneState
from utils.verbose import verbosePrint
from simulation.drone import Drone

if TYPE_CHECKING:
    from simulation.charger import Charger


class PotentialDronesAssignment(Ensemble):

    charger: 'Charger'

    def __init__(self, charger: 'Charger'):
        self.charger = charger

    def priority(self):
        return 2  # It is necessary to run this before AcceptedDronesAssignment. The order of PotentialDronesAssignment ensembles can be arbitrary as they don't influence each other.

    drones: List[Drone] = someOf(Drone)

    @drones.cardinality
    def drones(self):
        return 0, len(WORLD.drones)

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

    charger: 'Charger'

    def __init__(self, charger: 'Charger'):
        self.charger = charger

    def priority(self):
        return 1  # The order of AcceptedDronesAssignment ensembles can be arbitrary as they don't influence each other.

    drones: List[Drone] = someOf(Drone).withSelectionTimeEstimate().using(WORLD.acceptedDronesSelectionTimeEstimation)

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

    @drones.selectionTimeEstimate.input(IntEnumFeature(DroneState))
    def drone_state(self, drone):
        return drone.state

    @drones.selectionTimeEstimate.input(FloatFeature(0, math.sqrt(ENVIRONMENT.mapWidth ** 2 + ENVIRONMENT.mapHeight ** 2)))
    def charger_distance(self, drone):
        return self.charger.location.distance(drone.location)

    @drones.selectionTimeEstimate.input(FloatFeature(0, ENVIRONMENT.chargerCapacity))
    def accepted_drones_length(self, drone):
        return len(self.charger.acceptedDrones)

    @drones.selectionTimeEstimate.input(FloatFeature(0, ENVIRONMENT.chargerCapacity))
    def accepted_drones_missing_battery(self, drone):
        return sum([1 - drone.battery for drone in self.charger.acceptedDrones])

    @drones.selectionTimeEstimate.input(FloatFeature(0, ENVIRONMENT.chargerCapacity))
    def charging_drones_length(self, drone):
        return len(self.charger.chargingDrones)

    @drones.selectionTimeEstimate.input(FloatFeature(0, ENVIRONMENT.chargerCapacity))
    def charging_drones_missing_battery(self, drone):
        return sum([1 - drone.battery for drone in self.charger.chargingDrones])

    @drones.selectionTimeEstimate.input(FloatFeature(0, ENVIRONMENT.droneCount))
    def potential_drones_with_lower_battery(self, drone):
        return len([d for d in self.charger.potentialDrones if d.battery < drone.battery])

    # TODO: better features

    # @drones.selectionTimeEstimate.id
    # def id(self, drone):
    #     return drone.id

    @drones.selectionTimeEstimate.inputsFilter
    @drones.selectionTimeEstimate.targetsFilter
    def filter(self, drone):
        return drone not in self.charger.acceptedDrones  # don't collect the data if the drone was already selected in the previous step

    # @drones.selectionTimeEstimate.time
    # def time(self, drone):
    #     return WORLD.currentTimeStep

    def actuate(self):

        verbosePrint(f"Charging Ensemble: assigned {len(self.drones)} to {self.charger.id}", 4)

        for drone in self.drones:
            if drone in self.charger.acceptedDrones:
                continue
            WORLD.chargerLog.register([
                WORLD.currentTimeStep,
                drone.id,
                drone.battery,
                self.drones.selectionTimeEstimate.estimate(self, drone),
                drone.energyToFlyToCharger(),
                drone.timeToDoneCharging(),
                self.charger.id,
                len(self.charger.potentialDrones),
                len(self.charger.acceptedDrones),
                len(self.charger.chargingDrones),
            ])

        self.charger.acceptedDrones = self.drones


def getEnsembles(world):

    ensembles = \
        [PotentialDronesAssignment(charger) for charger in world.chargers] + \
        [AcceptedDronesAssignment(charger) for charger in world.chargers]

    return ensembles
