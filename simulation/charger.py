import random
from typing import List, Optional
import numpy as np

from simulation.components import Component, Point
from simulation.drone import DroneState


def getChargerClass(WORLD):

    Drone = WORLD.Drone

    class Charger(Component):
        """

        """
        # static Counter
        Count = 0

        def __init__(
                self,
                location,
                world):
            Charger.Count = Charger.Count + 1
            Component.__init__(self, location, world, Charger.Count)  # TODO: self.world can now be replaced by WORLD

            self.chargingRate = world.chargingRate
            self.chargerCapacity = world.chargerCapacity
            self.acceptedCapacity = world.chargerCapacity

            self.energyConsumed = 0

            self.potentialDrones: List[Drone] = []  # these belong to this charger and are not waiting or being charged
            self.acceptedDrones: List[Drone] = []  # drones accepted for charging, they move to the charger
            self.chargingDrones: List[Drone] = []  # drones currently being charged

        def startCharging(self, drone):
            """Drone is in the correct location and starts charging"""
            self.acceptedDrones.remove(drone)
            self.chargingDrones.append(drone)
            drone.state = DroneState.CHARGING

        def doneCharging(self, drone):
            drone.battery = 1
            self.chargingDrones.remove(drone)

        def timeToDoneCharging(self):
            maxBattery = max(map(lambda d: d.battery, self.chargingDrones), default=1)
            return (1 - maxBattery) / self.chargingRate

        def randomNearLocation(self):
            return Point(self.location.x + random.randint(1, 3), self.location.y + random.randint(1, 3))

        def provideLocation(self, drone):
            if drone in self.chargingDrones or drone in self.acceptedDrones:
                return self.location
            else:
                return self.randomNearLocation()

        def actuate(self):

            # charge the drones
            for drone in self.chargingDrones:
                drone.battery = drone.battery + self.chargingRate
                self.energyConsumed = self.energyConsumed + self.chargingRate
                if drone.battery >= 1:
                    self.doneCharging(drone)

            # move drones from accepted to charging
            freeChargingPlaces = self.chargerCapacity - len(self.chargingDrones)
            for i in range(freeChargingPlaces):
                if len(self.acceptedDrones) > 0:
                    for drone in self.acceptedDrones:
                        if drone.location == self.location:
                            self.startCharging(drone)

            # assign the target charger of the accepted drones
            for drone in self.acceptedDrones:
                drone.targetCharger = self

        def __repr__(self):
            return f"{self.id}: C={len(self.chargingDrones)}, A={len(self.acceptedDrones)}, P={len(self.potentialDrones)}"

        def report(self, iteration):
            pass

    return Charger
