import math
import random
from enum import Enum, IntEnum
from typing import List, Optional
import numpy as np


class Point:
    """
        The class represents a point on the world. X and Y are values from 0 to width or height.
        ...

        Attributes
        ----------
        x : int
            Value of current position on the map on X-axis
        y : int
            Value of current position on the map on X-axis

        Properties
        ----------
        X: int
            sets and gets the value of X, throws an exception if value < 0.
        Y: int
            sets and gets the value of Y, throws an exception if value < 0.

        Operands
        --------
        __sub__(p1,p2): returns (int,int)
            is called as p1-p2
            returns the result of p1-p2 where p1 and p2 are points.
        __eq__(p1,p2): returns bool
            is called as p1==p2
            returns the result of P1=P2 where P1 and P2 are points.
        __getitem__(point,index): returns int
             is called as point[index]
             if index=0, it returns point.x, otherwise it returns point.y
        
        Methods
        -------
        distance(other): returns int
            returns the distance between the current point and other point.
        
        static random(maxWidth, maxHeight): returns a Point
            creates a random point with margin of 1.

    """

    MaxWidth = 0
    MaxHeight = 0

    def __init__(
            self,
            x,
            y):
        self.x = x
        self.y = y

    def __sub__(self, other):
        return self.x - other.x, self.y - other.y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    # def __getitem__(self, index):
    #     if index==0:
    #         return self.x
    #     else:
    #         return self.y

    def __str__(self):
        return f"{self.x},{self.y}"

    def distance(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        dl = math.sqrt(dx * dx + dy * dy)
        return dl

    @staticmethod
    def random(x1, y1, x2, y2):
        return Point(random.randrange(x1, x2), random.randrange(y1, y2))

    @staticmethod
    def randomPoint():
        return Point(random.randrange(0, Point.MaxWidth), random.randrange(0, Point.MaxHeight))


class Field:
    """
        A Field that the simulation is running on.
        
        This defines an Area, which is technically a set of points.
        The set of points consist of 4 doubles as [x1, y1, x2, y2]

            (x1,y1) .__________
                    |          |
                    |__________|.(x2,y2)
                    
        Static Count for the Fields
    """

    # Field counter
    Count = 0

    topLeft: Point
    bottomRight: Point

    def __init__(
            self,
            pointLists,
            world):

        self.droneRadius = world.droneRadius
        self.world = world
        Field.Count = Field.Count + 1
        self.id = f"FIELD_{Field.Count}"
        self.topLeft = Point(pointLists[0], pointLists[1])
        self.bottomRight = Point(pointLists[2], pointLists[3])

        self.places = []
        self.protectingDrones = {}
        # new approach: how many protecting places there are
        for x in range(self.topLeft.x, self.bottomRight.x, self.droneRadius):
            for y in range(self.topLeft.y, self.bottomRight.y, self.droneRadius):
                self.places.append(Point(x + self.droneRadius / 2, y + self.droneRadius / 2))

    def locationPoints(self):
        points = []
        for x in range(self.topLeft.x, self.bottomRight.x):
            for y in range(self.topLeft.y, self.bottomRight.y):
                points.append(Point(x, y))

        return points

    # def randomPointOnField(self):
    #     return [randint(self.topLeft.x, self.bottomRight.x-1),randint(self.topLeft.y, self.bottomRight.y-1)]

    # a function to call and set all field points
    def isPointOnField(self, point):
        return (point.x >= self.topLeft.x and point.x < self.bottomRight.x) and (
                point.y >= self.topLeft.y and point.y < self.bottomRight.y)

    def closestDistanceToDrone(self, drone):
        distances = []
        for place in self.places:
            dx = place.x - drone.location.x
            dy = place.y - drone.location.y
            distances.append(math.sqrt(dx * dx + dy * dy))

        return min(distances)

    def assingPlace(self, drone):
        if drone not in self.protectingDrones:
            listOfEmptyPlaces = [place for place in self.places if
                                 place not in [self.protectingDrones[d] for d in self.protectingDrones]]
            if len(listOfEmptyPlaces) <= 0:
                return random.choice(self.places)
            self.protectingDrones[drone] = random.choice(listOfEmptyPlaces)

        return self.protectingDrones[drone]

    def unassign(self, drone):
        if drone in self.protectingDrones:
            del self.protectingDrones[drone]

    def randomLocation(self):
        return Point.random(self.topLeft.x, self.topLeft.y, self.bottomRight.x, self.bottomRight.y)

    # def closestDistanceToDrone (self,drone):
    #     minDistance = self.closestZoneToDrone(drone)
    #     return minDistance

    def randomPlaces(self, protectors):
        places = []
        # lenZones = len(self.zones)
        # interval = 1 if protectors > lenZones else int(lenZones/protectors)
        for i in range(protectors):
            randomZone = random.choice(self.places)
            places.append(Point(randomZone.x, randomZone.y))
        return places

    def __str__(self):
        return f"{self.id},{self.topLeft},{self.bottomRight}"


class Component:
    """
        Component class is used to represent A component on the map. 
        Components are all elements that are on the map such as Birds, Drones, Chargers and Charging Stations.

        Attributes
        ----------
        location : point.Point
            the current location of the agent on the map as [x,y]
        id : int
            the number of component created with this type to be used as ID.
        world : World 
                the world that the components are living in.
        Methods
        -------
        actuate()
            Abstract method that is developed on the derived classes level.
        
        locationPoints()
            return the current point as a list object.
    """
    location: Point

    id: str

    def __init__(
            self,
            location,
            world,
            componentID):
        """
            Initiate the Component object.
            After the derived type is identified, it gives a string ID
            For instance, if the derived class is a Drone, and there are already 4 drones,
            the new Drone will get `Drone_5` as its id.
            
        
            Parameters
            ----------
            location : point.Point
                the current location of the agent on the map as [x,y]. 
                It can be sent as an instace of Point or just a list of two points.

            id : int
                the number of component created with this type to be used as ID.

            world : World 
                the world that the components are living in.
        """
        child_type = type(self).__name__
        self.id = "%s_%d" % (child_type, componentID)
        self.world = world

        if isinstance(location, Point):
            self.location = location
        else:
            self.location = Point(location[0], location[1])

    def actuate(self):
        """
            An abstract method to be developed by the derived instances.
        """
        pass

    def locationPoints(self):
        """
            locationPoints()
                return the current point as a list object.
        """
        return [self.location.x, self.location.y]


class Agent(Component):
    """
        Extending component with mobility. 
        Agents can move, where components are all elements on a map that are constant or moving.
        Agent class is used to represent an Agent. 
        Agents are elements that move around a map and perform actions. 
        In this simulation, agents are Drones and Birds.

        ...

        Attributes
        ----------
        reporter : simulations.serializer.Report
            A static variable that points to the corresponding report object
        location : point.Point
            the current location of the agent on the map as [x,y]
         world : World 
                the world that the components are living in.
        speed : float
            the speed of the agent to be determined as point rate/tick.
        count : int
            the number of component created with this type to be used as ID.

        Methods
        -------
        report(timeStep)
            register the current status of the agent to the connected report object.
        
        move(target)
            move the current location toward the target
    """
    reporter = lambda agent, time: None
    header = ""

    def __init__(
            self,
            location,
            speed,
            world,
            count):
        """
            Initiate the Agent object.
            Parameters
            ----------
            location : point.Point
                the current location of the agent on the map as [x,y].

            speed : float
                the speed of the agent to be determined as point rate/tick.
            world : World 
                the world that the components are living in.
            count : int
                the number of component created with this type to be used as ID.
        """
        Component.__init__(self, location, world, count)
        self.speed = speed

    def move(self, target):
        """
            Moves the object from self.location to the target.
            Parameters
            ----------
            target : point.Point
                the target location on the map as [x,y].

            speed : float
                the speed of the agent to be determined as point rate/tick.
            count : int
                the number of component created with this type to be used as ID.
        """
        dx = target.x - self.location.x
        dy = target.y - self.location.y
        dl = math.sqrt(dx * dx + dy * dy)
        if dl >= self.speed:
            self.location = Point(self.location.x + dx * self.speed / dl,
                                  self.location.y + dy * self.speed / dl)
        else:
            self.location = target

    def report(self, timeStep):
        """
            Register the current situation of the agent in the Report object.
            Parameters
            ----------
            timeStep : int
                the current time step the simulation is running in.
        """
        Agent.reporter(self, timeStep)


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
        Component.__init__(self, location, world, Charger.Count)

        self.chargingRate = world.chargingRate
        self.chargerCapacity = world.chargerCapacity
        self.acceptedCapacity = world.chargerCapacity

        self.energyConsumed = 0

        self.potentialDrones: List[Drone] = []  # these belong to this charger and are not waiting or being charged
        self.acceptedDrones: List[Drone] = []  # drones accepted for charging, they move to the charger
        self.chargingDrones: List[Drone] = []  # drones currently being charged

        from estimators.charger_waiting_estimation import ChargerWaitingTimeEstimator  # just for the type annotation
        # the estimator is assigned later using assignWaitingTimeEstimator
        self.waitingTimeEstimator: Optional[ChargerWaitingTimeEstimator] = None
        self.waitingTimeEstimateCache = np.array([])
        self.waitingTimeEstimateCacheVersion = -1

    def assignWaitingTimeEstimator(self, estimator):
        """
        Parameters
        ----------
        estimator : common.charger_waiting_estimation.NeuralNetworkChargerWaitingTimeEstimation
        """
        self.waitingTimeEstimator = estimator

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

    def estimateWaitingTime(self, drone):
        if self.waitingTimeEstimateCacheVersion != self.world.currentTimeStep:
            self.updateWaitingTimeEstimateCache()
        droneIndex = self.potentialDrones.index(drone)
        return self.waitingTimeEstimateCache[droneIndex]

    def updateWaitingTimeEstimateCache(self):
        self.waitingTimeEstimateCache = self.waitingTimeEstimator.predictBatch(self, self.potentialDrones)
        self.waitingTimeEstimateCacheVersion = self.world.currentTimeStep

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


class BirdState(Enum):
    """
        An enumerate property for the birds.
        IDLE: a default state for birds, when they are out of fields.
        ATTACKING: a state where a bird has a field in mind, and attacking it.
        FLEEING: a state where a bird is running away from drones
    """

    IDLE = 0
    MOVING_TO_FIELD = 1
    OBSERVING = 2
    EATING = 3
    FLEEING = 4


class Bird(Agent):
    """
        The Bird Component

    """

    # # static Counter
    Count = 0

    StayProbability = 0.85
    AttackProbability = 0.12
    ReplaceProbability = 0.03

    # # all direction moves
    # mover : BirdMover
    def __init__(
            self,
            location,
            world):
        self.speed = world.birdSpeed

        Bird.Count = Bird.Count + 1
        Agent.__init__(self, location, self.speed, world, Bird.Count)

        self.state = BirdState.IDLE
        self.target = None
        self.field = None
        self.ate = 0

    def findRandomField(self):
        self.target = Point.random()

    def moveToNewField(self):
        self.field = random.choice(self.world.fields)
        self.target = self.field.randomLocation()

    def moveToNoField(self):
        self.field = None
        self.target = random.choice(self.world.emptyPoints)

    def moveWithinSameField(self):
        if self.field == None:
            self.moveToNewField()
        else:
            self.target = self.field.randomLocation()

    def actuate(self):
        if self.state == BirdState.IDLE:
            probability = random.random()
            # bird moves if we crossed threshold of StayProbability randomly
            if probability > Bird.StayProbability:
                probability -= Bird.StayProbability
                # to decide wether attack a farm or just move to another place
                if probability < Bird.AttackProbability:
                    self.moveToNewField()
                    self.state = BirdState.MOVING_TO_FIELD
                else:
                    self.moveToNoField()
                    self.state = BirdState.FLEEING

        if self.state == BirdState.MOVING_TO_FIELD:
            if self.location == self.target:
                self.state = BirdState.OBSERVING
            else:
                self.move(self.target)

        if self.state == BirdState.FLEEING:
            if self.location == self.target:
                self.state = BirdState.IDLE
            else:
                self.move(self.target)

        if self.state == BirdState.OBSERVING or self.state == BirdState.EATING:
            if self.world.isProtectedByDrone(self.location):
                self.moveToNoField()
                self.state = BirdState.FLEEING
            else:
                self.state = BirdState.EATING

        if self.state == BirdState.EATING:
            self.ate = self.ate + 1
            probability = random.random()
            if probability > Bird.StayProbability:
                probability -= Bird.StayProbability
                if probability < Bird.AttackProbability:
                    self.moveWithinSameField()
                    self.state = BirdState.MOVING_TO_FIELD
                else:
                    self.moveToNoField()
                    self.state = BirdState.FLEEING

    def __repr__(self):
        return f"{self.id}: state={self.state}, Total Ate={self.ate}"
