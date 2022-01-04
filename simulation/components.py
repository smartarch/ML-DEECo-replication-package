import math
import random
from enum import Enum

from simulation.world import ENVIRONMENT, WORLD
from estimators.estimate import Estimate


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
        return Point(random.randrange(0, ENVIRONMENT.mapWidth), random.randrange(0, ENVIRONMENT.mapHeight))


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

    def __init__(self, pointLists):

        self.droneRadius = ENVIRONMENT.droneRadius
        Field.Count = Field.Count + 1
        self.id = f"FIELD_{Field.Count}"
        self.topLeft = Point(pointLists[0], pointLists[1])
        self.bottomRight = Point(pointLists[2], pointLists[3])

        self.places = []
        self.protectingDrones = {}

        xCenters = math.ceil((self.bottomRight.x - self.topLeft.x) / self.droneRadius)
        yCenters = math.ceil((self.bottomRight.y - self.topLeft.y) / self.droneRadius)

        totalXCover = xCenters * self.droneRadius
        totalYCover = yCenters * self.droneRadius

        startX = int(self.topLeft.x - (totalXCover - (self.bottomRight.x - self.topLeft.x)) / 2)
        startY = int(self.topLeft.y - (totalYCover - (self.bottomRight.y - self.topLeft.y)) / 2)

        for i in range(xCenters):
            for j in range(yCenters):
                self.places.append(Point(startX, startY + (self.droneRadius * j)))
            startX = startX + self.droneRadius

        # # new approach: how many protecting places there are
        # for x in range(self.topLeft.x+(self.droneRadius/2), self.bottomRight.x, self.droneRadius):
        #     for y in range(self.topLeft.y+(self.droneRadius/2), self.bottomRight.y, self.droneRadius):
        #         self.places.append(Point(x + self.droneRadius, y + self.droneRadius))

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
        return self.topLeft.x <= point.x < self.bottomRight.x and \
               self.topLeft.y <= point.y < self.bottomRight.y

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

    def __init__(self, location, componentID):
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

        if isinstance(location, Point):
            self.location = location
        else:
            self.location = Point(location[0], location[1])

    def actuate(self):
        """
            An abstract method to be developed by the derived instances.
        """
        pass

    def collectEstimatesData(self):
        estimates = [fld for (fldName, fld) in type(self).__dict__.items()
                     if not fldName.startswith('__') and isinstance(fld, Estimate)]
        for estimate in estimates:
            estimate.collectInputs(self)
            estimate.collectTargets(self)

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

    def __init__(self, location, speed, count):
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
        Component.__init__(self, location, count)
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
            location):
        self.speed = ENVIRONMENT.birdSpeed

        Bird.Count = Bird.Count + 1
        Agent.__init__(self, location, self.speed, Bird.Count)

        self.state = BirdState.IDLE
        self.target = None
        self.field = None
        self.ate = 0

    def findRandomField(self):
        self.target = Point.random()

    def moveToNewField(self):
        self.field = random.choice(WORLD.fields)
        self.target = self.field.randomLocation()

    def moveToNoField(self):
        self.field = None
        self.target = random.choice(WORLD.emptyPoints)

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
            if WORLD.isProtectedByDrone(self.location):
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
