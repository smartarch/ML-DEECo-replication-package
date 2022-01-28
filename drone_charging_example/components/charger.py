import random
from typing import List, TYPE_CHECKING

from world import ENVIRONMENT, WORLD
from components.drone_state import DroneState
from ml_deeco.simulation import Component, Point

if TYPE_CHECKING:
    from components.drone import Drone


class Charger(Component):
    """
    The charger class represents the charger stations providing energy for drones in the simulation.
    The charging rate and capacity is defined in the WORLD and ENVIRONMENT objects shared with all components.

    Attributes
    ----------
    chargingRate : float
        The charging rate the charger is supposed to provide per time-step for landing drones.
    acceptedCapacity : int
        How many drones could be charged at the same time.
    potentialDrones : list
        The potential drones for the charger, the close drone ones despite their battery level.
    waitingDrones : list
        The list of drones that are in need of charging, but not accepted yet.
    acceptedDrones : list
        The list of accepted drones that are moving toward the charger.
    chargingDrones : list
        The list of drones that are being charged.
    """

    def __init__(self, location):
        """
        Initiate the charger instance with constant position on the map.

        Parameters
        ----------
        location : Point
            The location of the charger (constant).
        """
        Component.__init__(self, location)
        self.chargingRate = ENVIRONMENT.chargingRate
        self.acceptedCapacity = ENVIRONMENT.chargerCapacity
        self.potentialDrones: List[Drone] = []  # these belong to this charger and are not waiting or being charged
        self.waitingDrones: List[Drone] = []  # drones in need of being charged, waiting for acceptance
        self.acceptedDrones: List[Drone] = []  # drones accepted for charging, they move to the charger
        self.chargingDrones: List[Drone] = []  # drones currently being charged

    def startCharging(self, drone):
        """
        Drone is in the correct location and starts charging.

        Parameters
        ----------
        drone : Drone
            the drone state changes to CHARGING.
        """
        self.acceptedDrones.remove(drone)
        self.chargingDrones.append(drone)
        drone.state = DroneState.CHARGING

    def doneCharging(self, drone):
        """
        The drone battery gets full and it is done charging. Because of different rates, the battery might get > 1, therefore, this function makes the battery 1.

        Parameters
        ----------
        drone : Drone
            drone battery completes charging.
        """
        drone.battery = 1
        self.chargingDrones.remove(drone)

    def timeToDoneCharging(self, alreadyAccepted=0):
        """
        It computes the time that the charger will be free.

        Parameters
        ----------
        alreadyAccepted : int, optional
            The accepted drones.

        Returns
        -------
        float
            Time steps the charger will be free.
        """
        batteries = sorted(map(lambda d: d.battery, self.chargingDrones), reverse=True)
        if len(batteries) > alreadyAccepted:
            nthMaxBattery = batteries[alreadyAccepted]
        else:
            nthMaxBattery = 1
        return (1 - nthMaxBattery) / self.chargingRate

    def randomNearLocation(self):
        """
        finds random location near the charger.

        Returns
        -------
        Point
            a point near the charger.
        """
        return Point(self.location.x + random.randint(1, 3), self.location.y + random.randint(1, 3))

    def provideLocation(self, drone):
        """
        Gives the location of the charger to the drone.
        If the drone is accepted it can fly to the charger, the standby time is only due to unexpected latency in charging.

        Parameters
        ----------
        drone : Drone
            The drone which is asking for the location, to be checked in which queue this request is risen.

        Returns
        -------
        Point
            The point to be save in the target of drone.
        """
        if drone in self.chargingDrones or drone in self.acceptedDrones:
            return self.location
        else:
            return self.randomNearLocation()

    def actuate(self):
        """
        Performs the charger actions in all queues:
        chargingDrones:
            Charge them with a saturation provided by ENVIRONMENT.totalAvailableChargingEnergy
            For example if ENVIRONMENT.totalAvailableChargingEnergy = 0.12, and the charging rate is 0.04, then it means 3 drones could simultaneously change at one or different chargers.
            But for instance with 0.12, if there are 4 drones, they will get 0.03 charge rate.
            When the drone is done charging, its battery gets 1 and removed from queues.
        acceptedDrones:
            The charger will search and fill up the accepted drones with the capacity considered.
        """
        # charge the drones
        for drone in self.chargingDrones:
            # charging rate drops slightly with increased drones in charging
            totalChargingDrones = sum([len(charger.chargingDrones) for charger in WORLD.chargers])
            currentCharingRate = min(totalChargingDrones * ENVIRONMENT.chargingRate,
                                     ENVIRONMENT.totalAvailableChargingEnergy) / totalChargingDrones
            ENVIRONMENT.currentChargingRate = currentCharingRate
            drone.battery = drone.battery + currentCharingRate
            if drone.battery >= 1:
                self.doneCharging(drone)

        # move drones from accepted to charging
        freeChargingPlaces = self.acceptedCapacity - len(self.chargingDrones)
        for i in range(freeChargingPlaces):
            for drone in self.acceptedDrones:
                if drone.location == self.location:
                    self.startCharging(drone)
                    break

        # assign the target charger of the accepted drones
        for drone in self.acceptedDrones:
            drone.targetCharger = self

    def __repr__(self):
        """
        Represent the charger in one line.

        Returns
        -------
        str
            Prints information about all the queues of the charger.
        """
        return f"{self.id}: C={len(self.chargingDrones)}, A={len(self.acceptedDrones)}, W={len(self.waitingDrones)}, P={len(self.potentialDrones)}"
