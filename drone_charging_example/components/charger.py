import random
from typing import List, TYPE_CHECKING

from world import ENVIRONMENT, WORLD
from components.drone_state import DroneState

from ml_deeco.estimators import NumericFeature, CategoricalFeature, BinaryFeature, Estimate
from ml_deeco.simulation import Component, Point
from ml_deeco.utils import verbosePrint

if TYPE_CHECKING:
    from components.drone import Drone


class Charger(Component):
    """
    The drone charger component.
    """

    chargerUtilizationEstimate = Estimate().inTimeSteps(20).using(WORLD.chargerUtilizationEstimator)
    chargerFullEstimate = Estimate().inTimeSteps(20).using(WORLD.chargerFullEstimator)

    def __init__(self, location):
        Component.__init__(self, location)

        self.chargingRate = ENVIRONMENT.chargingRate
        self.chargerCapacity = ENVIRONMENT.chargerCapacity
        self.acceptedCapacity = ENVIRONMENT.chargerCapacity

        self.energyConsumed = 0

        self.potentialDrones: List[Drone] = []  # these belong to this charger and are not waiting or being charged
        self.waitingDrones: List[Drone] = []    # drones in need of being charged, waiting for acceptance
        self.acceptedDrones: List[Drone] = []   # drones accepted for charging, they move to the charger
        self.chargingDrones: List[Drone] = []   # drones currently being charged

    # region Estimates

    @chargerUtilizationEstimate.input(NumericFeature(0, ENVIRONMENT.droneCount))
    @chargerFullEstimate.input(NumericFeature(0, ENVIRONMENT.droneCount))
    def potential_drones(self):
        return len(self.potentialDrones)

    @chargerUtilizationEstimate.input(NumericFeature(0, ENVIRONMENT.droneCount))
    @chargerFullEstimate.input(NumericFeature(0, ENVIRONMENT.droneCount))
    def waiting_drones(self):
        return len(self.waitingDrones)

    @chargerUtilizationEstimate.input(NumericFeature(0, ENVIRONMENT.chargerCapacity))
    @chargerFullEstimate.input(NumericFeature(0, ENVIRONMENT.chargerCapacity))
    def accepted_drones(self):
        return len(self.acceptedDrones)

    @chargerUtilizationEstimate.input(NumericFeature(0, ENVIRONMENT.chargerCapacity))
    @chargerUtilizationEstimate.target(CategoricalFeature(list(range(ENVIRONMENT.chargerCapacity + 1))))
    @chargerFullEstimate.input(NumericFeature(0, ENVIRONMENT.chargerCapacity))
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
            # charging rate drops slightly with increased drones in charging
            totalChargingDrones = sum([len(charger.chargingDrones) for charger in WORLD.chargers])
            currentCharingRate =  min(totalChargingDrones*ENVIRONMENT.chargingRate,ENVIRONMENT.totalAvailableChargingEnergy) / totalChargingDrones
            ENVIRONMENT.currentChargingRate =  currentCharingRate
            drone.battery = drone.battery +  currentCharingRate
            self.energyConsumed = self.energyConsumed + currentCharingRate
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
