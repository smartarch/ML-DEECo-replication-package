import random
from typing import List, TYPE_CHECKING

from estimators.estimate import Estimate
from estimators.features import FloatFeature, CategoricalFeature, BinaryFeature
from simulation.world import ENVIRONMENT, WORLD
from simulation.components import Component, Point
from simulation.drone_state import DroneState
from utils.verbose import verbosePrint

if TYPE_CHECKING:
    from simulation.drone import Drone


class Charger(Component):
    """
    The drone charger component.
    """

    # static Counter
    Count = 0

    chargerUtilizationEstimate = Estimate().inTimeSteps(20).using(WORLD.chargerUtilizationEstimator)
    chargerFullEstimate = Estimate().inTimeSteps(20).using(WORLD.chargerFullEstimator)

    def __init__(self, location):
        Charger.Count = Charger.Count + 1
        Component.__init__(self, location, Charger.Count)

        self.chargingRate = ENVIRONMENT.chargingRate
        self.chargerCapacity = ENVIRONMENT.chargerCapacity
        self.acceptedCapacity = ENVIRONMENT.chargerCapacity

        self.energyConsumed = 0

        self.potentialDrones: List[Drone] = []  # these belong to this charger and are not waiting or being charged
        self.waitingDrones: List[Drone] = []    # drones in need of being charged, waiting for acceptance
        self.acceptedDrones: List[Drone] = []   # drones accepted for charging, they move to the charger
        self.chargingDrones: List[Drone] = []   # drones currently being charged

    # region Estimates

    @chargerUtilizationEstimate.input(FloatFeature(0, ENVIRONMENT.droneCount))
    @chargerFullEstimate.input(FloatFeature(0, ENVIRONMENT.droneCount))
    def potential_drones(self):
        return len(self.potentialDrones)

    @chargerUtilizationEstimate.input(FloatFeature(0, ENVIRONMENT.droneCount))
    @chargerFullEstimate.input(FloatFeature(0, ENVIRONMENT.droneCount))
    def waiting_drones(self):
        return len(self.waitingDrones)

    @chargerUtilizationEstimate.input(FloatFeature(0, ENVIRONMENT.chargerCapacity))
    @chargerFullEstimate.input(FloatFeature(0, ENVIRONMENT.chargerCapacity))
    def accepted_drones(self):
        return len(self.acceptedDrones)

    @chargerUtilizationEstimate.input(FloatFeature(0, ENVIRONMENT.chargerCapacity))
    @chargerUtilizationEstimate.target(CategoricalFeature(list(range(ENVIRONMENT.chargerCapacity + 1))))
    @chargerFullEstimate.input(FloatFeature(0, ENVIRONMENT.chargerCapacity))
    def charging_drones(self):
        return len(self.chargingDrones)

    @chargerFullEstimate.target(BinaryFeature())
    def charger_full(self):
        return len(self.chargingDrones) == self.chargerCapacity

    # endregion

    def startCharging(self, drone):
        """Drone is in the correct location and starts charging"""
        self.acceptedDrones.remove(drone)
        self.chargingDrones.append(drone)
        drone.state = DroneState.CHARGING

    def doneCharging(self, drone):
        drone.battery = 1
        self.chargingDrones.remove(drone)

    def timeToDoneCharging(self, alreadyAccepted=0):
        batteries = sorted(map(lambda d: d.battery, self.chargingDrones), reverse=True)
        if len(batteries) > alreadyAccepted:
            nthMaxBattery = batteries[alreadyAccepted]
        else:
            nthMaxBattery = 1
        return (1 - nthMaxBattery) / self.chargingRate

    def randomNearLocation(self):
        return Point(self.location.x + random.randint(1, 3), self.location.y + random.randint(1, 3))

    def provideLocation(self, drone):
        if drone in self.chargingDrones or drone in self.acceptedDrones:
            return self.location
        else:
            return self.randomNearLocation()

    def printEstimate(self):
        utilizationEstimate = self.chargerUtilizationEstimate()
        verbosePrint(utilizationEstimate, 4)
        isFullEstimate = self.chargerFullEstimate()
        verbosePrint(isFullEstimate, 4)

    def actuate(self):
        self.printEstimate()

        # charge the drones
        for drone in self.chargingDrones:
            drone.battery = drone.battery + self.chargingRate
            self.energyConsumed = self.energyConsumed + self.chargingRate
            if drone.battery >= 1:
                self.doneCharging(drone)

        # move drones from accepted to charging
        freeChargingPlaces = self.chargerCapacity - len(self.chargingDrones)
        for i in range(freeChargingPlaces):
            for drone in self.acceptedDrones:
                if drone.location == self.location:
                    self.startCharging(drone)
                    break

        # assign the target charger of the accepted drones
        for drone in self.acceptedDrones:
            drone.targetCharger = self

    def __repr__(self):
        return f"{self.id}: C={len(self.chargingDrones)}, A={len(self.acceptedDrones)}, W={len(self.waitingDrones)}, P={len(self.potentialDrones)}"

    def report(self, iteration):
        pass
