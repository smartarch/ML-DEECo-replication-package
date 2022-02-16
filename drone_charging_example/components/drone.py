import random
from typing import Optional, TYPE_CHECKING
from components.drone_state import DroneState
from world import ENVIRONMENT, WORLD
from ml_deeco.simulation import MovingComponent2D
if TYPE_CHECKING:
    from components.charger import Charger


class Drone(MovingComponent2D):
    """
    The drones protect the fields from birds by moving to the field and scaring the flocks of birds away.
    In programming perspective, drone components have access to shared `WORLD` and they can find the position to protect.
    In a real-life scenario, it is assumed that additional sensors will perform the detection of birds, and it can be read from them.

    Attributes
    ----------
    droneRadius: int
        Protecting radius of drone.
    droneMovingEnergyConsumption: float
        The energy consumption per time-step for drone moving.
    droneProtectingEnergyConsumption: float
        The energy consumption per time-step for protecting/standing drone.
    battery: float
        The battery percentage of the drone.
    target: Point2D
        The target location of the drone.
    targetField: Field
        The target field to protect.
    targetCharger: Charger
        The selected charger.
    closestCharger: Charger
        the closest charger which is picked by pre-assignment ensemble.
    alert: float
        If computed battery is below this value, it is assumed a critical battery level.
    state: DroneState
        IDLE: a default state for drones.
        PROTECTING: when the drones are protecting the fields.
        MOVING_TO_CHARGER: when the drones are moving/queuing for a charger.
        CHARGING: when the drones are being charged.
        TERMINATED: when the drones' battery is 0, and they do not operate anymore.
    """
    def __init__(self, location):
        """
        Creates a drone object with the given location and ENVIRONMENT settings.

        Parameters
        ----------
        location : Point2D
            Starting point for the drone.
        """
        self.droneRadius = ENVIRONMENT.droneRadius
        self.droneMovingEnergyConsumption = ENVIRONMENT.droneMovingEnergyConsumption
        self.droneProtectingEnergyConsumption = ENVIRONMENT.droneProtectingEnergyConsumption
        self.battery = 1 - (ENVIRONMENT.droneBatteryRandomize * random.random())
        self._state = DroneState.IDLE
        self.target = None
        self.targetField = None
        self.targetCharger: Optional[Charger] = None
        self.closestCharger: Optional[Charger] = None
        self.alert = 0.15
        super().__init__(location, ENVIRONMENT.droneSpeed)

    @property
    def state(self):
        """

        Returns
        -------
        DroneState
            IDLE: a default state for drones.
            PROTECTING: when the drones are protecting the fields.
            MOVING_TO_CHARGING: when the drones are moving/queuing for a charger.
            CHARGING: when the drones are being charged.
            TERMINATED: when the drones' battery is 0, and they do not operate anymore.
        """
        return self._state

    @state.setter
    def state(self, value):
        """
        Sets the drone state.

        Parameters
        ----------
        value : DroneState
        """
        self._state = value

    def timeToEnergy(self, time, consumptionRate=None):
        """
        Computes the amount of energy which is consumed in the given time.

        Parameters
        ----------
        time : int
            The time (in time steps).
        consumptionRate : float, optional
            The battery consumption per time step, defaults to `self.droneMovingEnergyConsumption`.

        Returns
        -------
        float
            The amount of energy consumed in given time.
        """
        if consumptionRate is None:
            consumptionRate = self.droneMovingEnergyConsumption
        return time * consumptionRate

    def findClosestCharger(self):
        """
        Finds the closest charger comparing the drone distance and WORLD chargers.

        Returns
        -------
        charger
            The closest charger to the drone.
        """
        return min(WORLD.chargers, key=lambda charger: self.location.distance(charger.location))

    def timeToFlyToCharger(self, charger=None):
        """
        Computes the time needed to get to the charger or the closest charger.

        Parameters
        ----------
        charger : Charger, optional
            Specify the charger for measuring the distance, defaults to `self.closestCharger`.

        Returns
        -------
        float
            The time steps needed to fly to the (given) charger.
        """
        if charger is None:
            charger = self.closestCharger
        return self.location.distance(charger.location) / self.speed

    def energyToFlyToCharger(self, charger=None):
        """

        Computes the energy needed to fly to the specified charger.

        Parameters
        ----------
        charger : Charger, optional
             Specify the charger for measuring the distance.

        Returns
        -------
        float
            The energy required to fly to the closest or given charger.
        """
        return self.timeToEnergy(self.timeToFlyToCharger(charger))

    def computeBatteryAfterTime(self, time: int):
        """
        Computes the battery after given time (assuming the `self.droneMovingEnergyConsumption` energy consumption per time step).

        Parameters
        ----------
        time : int
            Time steps.

        Returns
        -------
        float
            Battery after spending energy in given time steps.
        """
        return self.battery - self.timeToEnergy(time)

    def timeToDoneCharging(self):
        """
        Computes how long it will take to fly to the closest charger and get fully charged, assuming the charger is free.

        Returns
        -------
        int
            The time which the drone will be done charging.
        """
        batteryWhenGetToCharger = self.battery - self.energyToFlyToCharger()
        timeToCharge = (1 - batteryWhenGetToCharger) * self.closestCharger.chargingRate
        return self.timeToFlyToCharger() + timeToCharge

    def needsCharging(self, timeToStartCharging: int):
        """
        Checks if the drone needs charging assuming it will take `timeToStartCharging` time steps to get to the charger and start charging.

        In ML-Based model, the waiting time is predicted and is part of the `timeToStartCharging`.
        If computed battery is below threshold, the function returns true.

        Parameters
        ----------
        timeToStartCharging : int
            The time the drone needs to get to the charger (and possibly wait) and start charging.

        Returns
        -------
        bool
            Whether the drone needs charging or does not.
        """
        if self.state == DroneState.TERMINATED:
            return False
        futureBattery = self.computeBatteryAfterTime(timeToStartCharging)
        if futureBattery < 0:
            return False
        return futureBattery < self.alert

    def checkBattery(self):
        """
        It checks the battery if is below or equal to 0, it is assumed the drone is dead and it will get removed from the given tasks.
        """
        if self.battery <= 0:
            self.battery = 0
            self.state = DroneState.TERMINATED
            if self.targetField is not None:
                self.targetField.unassign(self)
                
    def move(self):
        """
        It moves the drone by calling the (super) Agent moving function, with addition of decreasing the battery in moving consumption rate.
        """
        self.battery = self.battery - self.droneMovingEnergyConsumption
        super().move(self.target)

    def actuate(self):
        """
        It performs the actions of the drone in one time-step.
        For each state it performs differently:
        TERMINATED:
            Returns, no actions.
        IDLE or PROTECTING:
            checks the targetCharger, because if the charger is set it means the drone needs charging; the state wil be changed to MOVING_TO_CHARGER.
            If not, then it checks the targetField, if it is set, it means that the drone is required on a filed; the state will be changed to MOVING_TO_FIELD.
            If the drone targets are not set, it remains IDLE, and will not consume battery. It is assumed, that it landed or returned to hanger in a real-life scenario.
        MOVING_TO_CHARGER:
            It removes the drone from the field, and start moving toward the charger, with moving energy consumption rate. When it reached to the charger, the drone will consume standing energy until it is landed on the charger. We are not alway certian that by the time drone gets to the charger it will be free. This is due to the fact, the charging rate is changed regarding how many other drones are being charged somewhere else.
        MOVING_TO_FIELD:
            Starts moving toward the field and when reached, it will change the state to PROTECTING.
        CHARGING:
            The drone starts being charged by the charger until the battery level gets to 1. When the battery is ful, the state will be changed to IDLE.  
        
        In each timestep it is checking the battery, to see if the drone is still alive.
        """
        if self.state == DroneState.TERMINATED:
            return
        if self.state < DroneState.MOVING_TO_CHARGER:  # IDLE, PROTECTING or MOVING TO FIELD
            if self.targetCharger is not None:
                self.state = DroneState.MOVING_TO_CHARGER
            else:
                if self.targetField is None:
                    self.state = DroneState.IDLE
                    return
                self.target = self.targetField.assignPlace(self)
                self.state = DroneState.MOVING_TO_FIELD

        if self.state == DroneState.MOVING_TO_CHARGER:
            if self.targetField is not None:
                self.targetField.unassign(self)
            self.target = self.targetCharger.provideLocation(self)
            if self.location != self.targetCharger.location:
                self.move()
            else:
                self.battery = self.battery - self.droneProtectingEnergyConsumption

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
        """
        Checks if the given point is protected by the drone.

        Parameters
        ----------
        point : Point2D
            A given point on the field.

        Returns
        -------
        bool
            True if the given point is within the radius of the drone and drone's state is protecting.
        """
        return (self.state == DroneState.PROTECTING or self.state == DroneState.MOVING_TO_FIELD) and self.location.distance(
            point) <= self.droneRadius

    def protectRadius(self):
        """
        Gives the radius of the drone as form of rectangle to be presented in visualization.

        Returns
        -------
        Point2D, Point2D, Point2D, Point2D
            Top X, Top Y, Bottom X and Bottom Y
        """
        startX = self.location.x - self.droneRadius
        endX = self.location.x + self.droneRadius
        startY = self.location.y - self.droneRadius
        endY = self.location.y + self.droneRadius
        startX = 0 if startX < 0 else startX
        startY = 0 if startY < 0 else startY
        return startX, startY, endX, endY

    def __repr__(self):
        """
        Returns
        -------
        string
            Represent the drone instance in one line.
        """
        return f"{self.id}: state={str(self.state)}, battery={self.battery}"
