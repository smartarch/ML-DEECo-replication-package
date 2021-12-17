import random
from enum import IntEnum
from typing import Optional

from simulation.components import Agent


class DroneState(IntEnum):
    """
        An enumerate property for the drones.
        IDLE: a default state for drones.
        PROTECTING: when the drones are protecting the zones.
        MOVING_TO_CHARGING: when the drones are moving/queuing for a charger.
        CHARGIN: when the drones are being chareged.
        TERMINATED: when the drone's battery is below 0 and they do not operate anymore.
    """

    IDLE = 0
    PROTECTING = 1
    MOVING_TO_FIELD = 2
    MOVING_TO_CHARGER = 3
    CHARGING = 4
    TERMINATED = 5


class Drone(Agent):
    """
        The drone class represent the active drones that are in the field.
        Location: type of a Point (x,y) in a given world.
        Battery: a level that shows how much of battery is left. 1 means full and 0 means empty.
        State: the state of a Drone as following:
            0 IDLE: a default state for drones.
            1 PROTECTING: when the drones are protecting the zones.
            2 MOVING_TO_CHARGING: when the drones are moving/queuing for a charger.
            3 CHARGIN: when the drones are being chareged.
            4 TERMINATED: when the drone's battery is below 0 and they do not operate anymore.
        Target: is the target component, it could be a place, a charger, a bird, or anything else.
        Static Count for the Drones
    """
    # static Counter
    Count = 0

    def __init__(
            self,
            location,
            world):

        self.droneRadius = world.droneRadius
        self.droneSpeed = world.droneSpeed
        self.droneMovingEnergyConsumption = world.droneMovingEnergyConsumption
        self.droneProtectingEnergyConsumption = world.droneProtectingEnergyConsumption

        self.battery = 1 - (world.droneBatteryRandomize * random.random())
        self.state = DroneState.IDLE

        self.target = None
        self.targetField = None
        from simulation.charger import Charger  # just for type annotation
        self.targetCharger: Optional[Charger] = None
        self.closestCharger: Optional[Charger] = None
        self.alert = 0.2
        self.world = world

        Drone.Count = Drone.Count + 1
        Agent.__init__(self, location, self.droneSpeed, world, Drone.Count)

    def findClosestCharger(self):
        return min(self.world.chargers, key=lambda charger: self.location.distance(charger.location))

    def timeToFlyToCharger(self, charger=None):
        if charger is None:
            charger = self.closestCharger

        return self.location.distance(charger.location) / self.speed

    def energyToFlyToCharger(self, charger=None):
        return self.timeToFlyToCharger(charger) * self.droneMovingEnergyConsumption

    def estimateWaitingEnergy(self, charger):
        # TODO (MA): Change or Find a way for the drone to wait (Energy)
        return charger.estimateWaitingTime(self) * self.droneProtectingEnergyConsumption

    # TODO: give this function a better name
    # TODO(MT): move the energyRequiredToGetToCharger inside the estimate -> update "Baseline 0" to "Baseline energyRequiredToGetToCharger"
    def computeFutureBattery(self):
        return self.battery \
               - self.energyToFlyToCharger() \
               - self.estimateWaitingEnergy(self.closestCharger)

    def timeToDoneCharging(self):
        timeToGetToCharger = self.closestCharger.location.distance(self.location) / self.speed
        batteryWhenGetToCharger = self.battery - timeToGetToCharger * self.droneMovingEnergyConsumption
        timeToCharge = (1 - batteryWhenGetToCharger) * self.closestCharger.chargingRate
        return timeToGetToCharger + timeToCharge

    def needsCharging(self):
        if self.state == DroneState.TERMINATED:
            return False

        futureBattery = self.computeFutureBattery()

        if futureBattery < 0:
            return False

        return futureBattery < self.alert

    def isChargingOrWaiting(self):
        """True if the drone is being charged, or it is already assigned to a charger queue and is waiting."""
        return self.state == DroneState.CHARGING or \
               self.state == DroneState.MOVING_TO_CHARGER

    # # TODO: this is wrong: why `1 - value` ?
    # def batteryAfterGetToCharger(self, charger):
    #     value = self.battery - self.energyRequiredToGetToCharger(charger.location)
    #     if value < 0.0001:  # not feasible to get to this charger
    #         return 1
    #     else:
    #         return 1 - value

    # def isBatteryCritical(self,chargerLocation):
    #     return self.battery - self.energyRequiredToCharge(chargerLocation) <= self.alert

    def checkBattery(self):
        if self.battery <= 0:
            self.battery = 0
            self.state = DroneState.TERMINATED
            if self.targetField is not None:
                self.targetField.unassign(self)

            # if self.closestCharger is not None:
            #     self.closestCharger.droneDied(self)

    def move(self):
        self.battery = self.battery - self.droneMovingEnergyConsumption
        super().move(self.target)

    def actuate(self):
        if self.state == DroneState.TERMINATED:
            return
        if self.state < DroneState.MOVING_TO_CHARGER:  # IDLE, PROTECTING or MOVING TO FIELD
            if self.targetCharger is not None:
                self.state = DroneState.MOVING_TO_CHARGER
                if self.targetField is not None:
                    self.targetField.unassign(self)
            else:
                if self.targetField is None:
                    self.state = DroneState.IDLE
                    return
                self.target = self.targetField.assingPlace(self)
                self.state = DroneState.MOVING_TO_FIELD

        if self.state == DroneState.MOVING_TO_CHARGER:
            self.target = self.targetCharger.provideLocation(self)
            if self.location != self.targetCharger.location:
                self.move()

        if self.state == DroneState.MOVING_TO_FIELD:
            if self.location == self.target:
                self.state = DroneState.PROTECTING
                self.battery = self.battery - self.droneProtectingEnergyConsumption
            else:
                self.move()
        if self.state == DroneState.CHARGING:
            if self.battery >= 1:
                self.targetCharger = None
                self.state = DroneState.IDLE
        self.checkBattery()

    def isProtecting(self, point):
        return (self.state == DroneState.PROTECTING or self.state == DroneState.MOVING_TO_FIELD) and self.location.distance(
            point) <= self.droneRadius

    def protectRadius(self):
        startX = self.location.x - self.droneRadius
        endX = self.location.x + self.droneRadius
        startY = self.location.y - self.droneRadius
        endY = self.location.y + self.droneRadius
        startX = 0 if startX < 0 else startX
        startY = 0 if startY < 0 else startY
        endX = self.world.mapWidth - 1 if endX >= self.world.mapWidth else endX
        endY = self.world.mapHeight - 1 if endY >= self.world.mapHeight else endY
        return (startX, startY, endX, endY)

    def __repr__(self):
        return f"{self.id}: state={str(self.state)}, battery={self.battery}"