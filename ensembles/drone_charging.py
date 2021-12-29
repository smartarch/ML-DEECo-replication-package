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


# The order of the ensemble is:
#  1. PotentialDronesAssignment
#  2. WaitingDronesAssignment
#  3. AcceptedDronesAssignment


class PotentialDronesAssignment(Ensemble):

    charger: 'Charger'

    def __init__(self, charger: 'Charger'):
        self.charger = charger

    def priority(self):
        return 3

    drones: List[Drone] = someOf(Drone)

    @drones.cardinality
    def drones(self):
        return 0, ENVIRONMENT.droneCount

    @drones.select
    def drones(self, drone, otherEnsembles):
        return drone.state not in (DroneState.TERMINATED, DroneState.MOVING_TO_CHARGER, DroneState.CHARGING) and \
            drone.findClosestCharger() == self.charger

    def actuate(self):
        self.charger.potentialDrones = self.drones
        for drone in self.drones:
            drone.closestCharger = self.charger

        verbosePrint(f"PotentialDronesAssignment: assigned {len(self.drones)} to {self.charger.id}", 4)


# estimator(komp instance, atribut)
# estimator(typ ensemblu, parametry konstruktoru, fnValue) [ regrese ]
# - atT+X = futureValue
# (- timeToC = jak dlouho nez např. regrese > hodnota)
# 
# estimator(komp instance, fnClassify)
# estimator(typ ensemblu, parametry konstruktoru, fnClassify) [ klasifikace ]
# - timeToC = jak dlouho nez klasifikace vrati C
# - isAtT+X = T/F -- např. membership
# 
# fnSplneno = drone je v te ensemble instanci


class WaitingDronesAssignment(Ensemble):

    charger: 'Charger'

    def __init__(self, charger: 'Charger'):
        self.charger = charger

    def priority(self):
        return 2

    drones: List[Drone] = someOf(Drone).withTimeToMembershipInOtherEnsembleEstimate().using(WORLD.waitingTimeEstimator)

    @drones.cardinality
    def drones(self):
        return 0, ENVIRONMENT.droneCount

    @drones.select
    def drones(self, drone, otherEnsembles):
        if drone.state == DroneState.TERMINATED:
            return False

        waitingTimeEstimate = self.drones.timeToMembershipEstimate(drone)
        timeToFlyToCharger = drone.timeToFlyToCharger()

        # needs charging
        return drone in self.charger.potentialDrones and \
            drone.needsCharging(waitingTimeEstimate + timeToFlyToCharger)

    @drones.timeToMembershipEstimate.input(FloatFeature(0, 1))
    def battery(self, drone):
        return drone.battery

    @drones.timeToMembershipEstimate.input(IntEnumFeature(DroneState))
    def drone_state(self, drone):
        return drone.state

    @drones.timeToMembershipEstimate.input(FloatFeature(0, math.sqrt(ENVIRONMENT.mapWidth ** 2 + ENVIRONMENT.mapHeight ** 2)))
    def charger_distance(self, drone):
        return self.charger.location.distance(drone.location)

    @drones.timeToMembershipEstimate.input(FloatFeature(0, ENVIRONMENT.chargerCapacity))
    def accepted_drones_length(self, drone):
        return len(self.charger.acceptedDrones)

    @drones.timeToMembershipEstimate.input(FloatFeature(0, ENVIRONMENT.chargerCapacity))
    def accepted_drones_missing_battery(self, drone):
        return sum([1 - drone.battery for drone in self.charger.acceptedDrones])

    @drones.timeToMembershipEstimate.input(FloatFeature(0, ENVIRONMENT.chargerCapacity))
    def charging_drones_length(self, drone):
        return len(self.charger.chargingDrones)

    @drones.timeToMembershipEstimate.input(FloatFeature(0, ENVIRONMENT.chargerCapacity))
    def charging_drones_missing_battery(self, drone):
        return sum([1 - drone.battery for drone in self.charger.chargingDrones])

    @drones.timeToMembershipEstimate.input(FloatFeature(0, ENVIRONMENT.droneCount))
    def potential_drones_with_lower_battery(self, drone):
        return len([d for d in self.charger.potentialDrones if d.battery < drone.battery])

    # TODO: better features

    @drones.timeToMembershipEstimate.inputsFilter
    def filter(self, drone):
        return drone not in self.charger.waitingDrones  # don't collect the data if the drone was already selected in the previous step

    @drones.timeToMembershipEstimate.targetsFilter
    def filter(self, drone):
        return drone not in self.charger.acceptedDrones  # don't collect the data if the drone was already selected in the previous step

    def actuate(self):

        verbosePrint(f"WaitingDronesAssignment: assigned {len(self.drones)} to {self.charger.id}", 4)

        self.charger.waitingDrones = self.drones


class AcceptedDronesAssignment(Ensemble):

    charger: 'Charger'

    def __init__(self, charger: 'Charger'):
        self.charger = charger

    def priority(self):
        return 1  # The order of AcceptedDronesAssignment ensembles can be arbitrary as they don't influence each other.

    drones: List[Drone] = someOf(Drone)

    @drones.cardinality
    def drones(self):
        return 0, self.charger.acceptedCapacity

    @drones.select
    def drones(self, drone, otherEnsembles):
        if drone.state == DroneState.TERMINATED:
            return False

        # was accepted before or needs charging (is waiting) and the charger will be free
        return drone in self.charger.acceptedDrones or \
            drone in self.charger.waitingDrones and \
            self.charger.timeToDoneCharging(len(self.drones)) <= drone.timeToFlyToCharger()

    @drones.priority
    def drones(self, drone):
        if drone in self.charger.acceptedDrones:
            return 1  # keep the accepted drones from previous time steps
        return -drone.timeToDoneCharging()

    def actuate(self):

        verbosePrint(f"AcceptedDronesAssignment: assigned {len(self.drones)} to {self.charger.id}", 4)

        for drone in self.drones:
            if drone in self.charger.acceptedDrones:
                continue
            waitingDronesAssignment = next(filter(lambda e: isinstance(e, WaitingDronesAssignment) and e.charger == self.charger, ensembles))
            WORLD.chargerLog.register([
                WORLD.currentTimeStep,
                drone.id,
                drone.battery,
                WaitingDronesAssignment.drones.timeToMembershipEstimate.estimate(waitingDronesAssignment, drone),
                drone.energyToFlyToCharger(),
                drone.timeToDoneCharging(),
                self.charger.id,
                len(self.charger.potentialDrones),
                len(self.charger.waitingDrones),
                len(self.charger.acceptedDrones),
                len(self.charger.chargingDrones),
            ])

        self.charger.acceptedDrones = self.drones


WaitingDronesAssignment.drones.bindTo(AcceptedDronesAssignment.drones)


ensembles: List[Ensemble]


def getEnsembles(world):
    global ensembles

    ensembles = \
        [PotentialDronesAssignment(charger) for charger in world.chargers] + \
        [WaitingDronesAssignment(charger) for charger in world.chargers] + \
        [AcceptedDronesAssignment(charger) for charger in world.chargers]

    return ensembles
