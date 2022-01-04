import random
from typing import Optional, TYPE_CHECKING

from estimators.estimate import Estimate
from estimators.features import FloatFeature, IntEnumFeature
from simulation.components import Agent
from simulation.drone_state import DroneState
from simulation.world import ENVIRONMENT, WORLD
from utils.verbose import verbosePrint

if TYPE_CHECKING:
    from simulation.charger import Charger


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

    futureBatteryEstimate = Estimate().inTimeSteps(50).using(WORLD.droneBatteryEstimator)

    def __init__(self, location):

        self.droneRadius = ENVIRONMENT.droneRadius
        self.droneSpeed = ENVIRONMENT.droneSpeed
        self.droneMovingEnergyConsumption = ENVIRONMENT.droneMovingEnergyConsumption
        self.droneProtectingEnergyConsumption = ENVIRONMENT.droneProtectingEnergyConsumption

        self.battery = 1 - (ENVIRONMENT.droneBatteryRandomize * random.random())
        self._state = DroneState.IDLE

        self.target = None
        self.targetField = None
        self.targetCharger: Optional[Charger] = None
        self.closestCharger: Optional[Charger] = None
        self.alert = 0.2

        Drone.Count = Drone.Count + 1
        Agent.__init__(self, location, self.droneSpeed, Drone.Count)

    # region Estimates

    @futureBatteryEstimate.input(FloatFeature(0, 1))
    def battery(self):
        return self.battery

    @futureBatteryEstimate.input(IntEnumFeature(DroneState))
    def drone_state(self):
        return self.state

    @futureBatteryEstimate.target()
    def battery(self):
        return self.battery

    @futureBatteryEstimate.inputsFilter
    @futureBatteryEstimate.targetsFilter
    def not_terminated(self):
        return self.state != DroneState.TERMINATED

    # endregion

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value

    def timeToEnergy(self, time, consumptionRate=None):
        if consumptionRate is None:
            consumptionRate = self.droneMovingEnergyConsumption
        return time * consumptionRate

    def findClosestCharger(self):
        return min(WORLD.chargers, key=lambda charger: self.location.distance(charger.location))

    def timeToFlyToCharger(self, charger=None):
        if charger is None:
            charger = self.closestCharger

        return self.location.distance(charger.location) / self.speed

    def energyToFlyToCharger(self, charger=None):
        return self.timeToEnergy(self.timeToFlyToCharger(charger))

    def computeBatteryAfterTime(self, time: int):
        return self.battery - self.timeToEnergy(time)

    def timeToDoneCharging(self):
        """How long it will take to fly to the closest charger and get fully charged, assuming the charger is free."""
        batteryWhenGetToCharger = self.battery - self.energyToFlyToCharger()
        timeToCharge = (1 - batteryWhenGetToCharger) * self.closestCharger.chargingRate
        return self.timeToFlyToCharger() + timeToCharge

    def needsCharging(self, timeToStartCharging: int):
        if self.state == DroneState.TERMINATED:
            return False

        futureBattery = self.computeBatteryAfterTime(timeToStartCharging)

        if futureBattery < 0:
            return False

        return futureBattery < self.alert

    def futureBatteryAlert(self):
        if self.state == DroneState.TERMINATED:
            return

        futureBattery = self.futureBatteryEstimate()
        if futureBattery < self.alert:
            verbosePrint("Alert: predicted futureBattery is low", 4)

    def checkBattery(self):
        if self.battery <= 0:
            self.battery = 0
            self.state = DroneState.TERMINATED
            if self.targetField is not None:
                self.targetField.unassign(self)

    def move(self):
        self.battery = self.battery - self.droneMovingEnergyConsumption
        super().move(self.target)

    def actuate(self):
        self.futureBatteryAlert()

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
        endX = ENVIRONMENT.mapWidth - 1 if endX >= ENVIRONMENT.mapWidth else endX
        endY = ENVIRONMENT.mapHeight - 1 if endY >= ENVIRONMENT.mapHeight else endY
        return startX, startY, endX, endY

    def __repr__(self):
        return f"{self.id}: state={str(self.state)}, battery={self.battery}"
