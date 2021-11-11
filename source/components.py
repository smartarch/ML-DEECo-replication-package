"""
    This file contains the base classes and formal defintions for each type that are being dealt with it in the research.\
    The classes are:
        1. Component Class: an abstract class that simply parnets all component objects on the field.
            A. Drone
            B. Charger
            C. Bird

"""
from enum import Enum
from exceptions import PointNotOnMapError 
import simulation
from random import randint, random , choice
import math

class Point:
    """
        The class represents a point on the world.
        X and Y are values from 0 to 1, for instance 0.5 meaning at the center of map.
        The default values at the start of each Point is 0.5 and 0.5
        Please keep in mind that the X and Y must be a value, where  0 < value < 1
    """

    _x: float
    _y: float

    def __init__ (
                    self,
                    x,
                    y):
        self.x = x
        self.y = y

    @property
    def x (self):
        return self._x
    
    @x.setter
    def x(self, value):
        if value<0:
            raise PointNotOnMapError(value)
        self._x = value
    
    @property
    def y (self):
        return self._y
    
    @y.setter
    def y(self, value):
        if value<0:
            raise PointNotOnMapError(value)
        self._y = value

    def __sub__ (self, other):
        return self.x-other.x , self.y-other.y
    
    def __eq__(self, other):
        return self[0]==other[0] and self[1]==other[1]
    def __str__ (self):
        return f"{self._x},{self.y}"
    
    def __getitem__(self, index):
        if index==0:
            return self._x
        else:
            return self._y

    def random (maxWidth,maxHeight):
        return Point(randint(1,maxWidth-1),randint(1,maxHeight-1))


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
    World = None

    topLeft : Point
    bottomRight : Point


    def __init__ (
                    self,
                    pointLists):
        Field.Count = Field.Count +1
        self.id = f"FIELD_{Field.Count}"
        self.topLeft = Point(pointLists[0],pointLists[1])
        self.bottomRight = Point(pointLists[2],pointLists[3])

    @property
    def places(self):
        return self.locationPoints()

    # return all locations
    def locationPoints(self):
        points = []
        for x in range(self.topLeft.x,self.bottomRight.x):
            for y in range(self.topLeft.y,self.bottomRight.y):
                points.append ([x,y])

        return points

    def randomPointOnField(self):
        return [randint(self.topLeft.x, self.bottomRight.x-1),randint(self.topLeft.y, self.bottomRight.y-1)]
    
    # a function to call and set all field points
    def isPointOnField (self,point):
        return (point.x >= self.topLeft.x and point.x < self.bottomRight.x) and (point.y >= self.topLeft.y and point.y < self.bottomRight.y)

    def __str__ (self):
        return f"{self.id},{self.topLeft},{self.bottomRight}"
        
class Component:
    """
        The abstract class for the Chargers, Drones, Flocks or any other component lives on the field.
        ID is auto assigned as the TYPE NAME ID  
    """
    location: Point
    World = None

    id: str
    def __init__(
                    self,
                    location,
                    id=0):
        child_type = type(self).__name__
        self.id = "%s_%d"%(child_type, id)

        if isinstance(location,Point):
            self.location = location
        else:
            self.location = Point(location[0], location[1])

    def actuate(self):
        pass

    def locationPoints(self):
        return [self.location.x,self.location.y]


class Agent (Component):

    reporter = None

    def __init__ (
                    self,
                    location,
                    speed,
                    count):

        Component.__init__(self,location,count)

        self.speed = speed

    def move(self, target):
        dx = target[0] - self.location[0]
        dy = target[1] - self.location[1]
        dl = math.sqrt(dx * dx + dy * dy)
        randomFactor = random()+1
        if dl >= self.speed * randomFactor:
            self.location = Point(int(self.location[0] + dx * self.speed * randomFactor / dl),
                                int(self.location[1] + dy * self.speed * randomFactor / dl))
        else:
            self.location = target

    def report(self,timeStep):
        Agent.reporter(self,timeStep)


class DroneState(Enum):
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
    MOVING_FIELD = 2
    MOVING_CHARGER = 3
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
    ChargingAlert = 0.05

    def __init__ (
                    self, 
                    location,
                    speed=1,
                    energy=0.001):

        Drone.Count = Drone.Count + 1
        Agent.__init__(self,location,speed,Drone.Count)
        
        #self.location = location
        self.battery = 1 - (0.1 * random())
        self.state = DroneState.IDLE
        self.target = None
        self.energy = energy
        self.radius = 5 # 5 points around it
        self.targetFieldPosition = None
        self.targetCharger = None

    def actuate(self):
        self.battery -= self.energy
        if self.battery<=0:
            self.state = DroneState.TERMINATED

        if self.state == DroneState.IDLE or self.state == DroneState.PROTECTING:
            if self.criticalBattery():
                if self.targetCharger!=None:
                    self.target = self.targetCharger.location
                    self.state = DroneState.MOVING_CHARGER
                else:
                    pass
            else:
                self.target = self.targetFieldPosition
                self.state = DroneState.MOVING_FIELD

        if self.state == DroneState.MOVING_CHARGER:
            if self.targetCharger!=None:
                if self.location == self.target:
                    self.state = DroneState.CHARGING
                else:
                    self.move(self.target)
            else:
                pass

        if self.state == DroneState.MOVING_FIELD:
            if self.targetFieldPosition!=None:
                if self.location == self.target:
                    self.state = DroneState.PROTECTING
                else:
                    self.move(self.target)
            else:
                pass
            
        if self.state == DroneState.CHARGING:
            self.targetCharger.charge(self)
            if self.battery >=1 :
                self.state = DroneState.IDLE

    
    def criticalBattery (self):
        return self.battery -  self.energyNeededToMoveToCharger() < Drone.ChargingAlert

    def protectRadius(self):
        startX = self.location[0]-self.radius
        endX = self.location[0]+self.radius
        startY = self.location[1]-self.radius
        endY = self.location[1]+self.radius
        startX = 0 if startX <0 else startX
        startY = 0 if startY <0 else startY
        endX = simulation.World.Width-1 if endX>=simulation.World.Width else endX
        endY = simulation.World.Height-1 if endY>=simulation.World.Height else endY
        return (startX,startY,endX,endY)
    
    # return all points that are protected by this drone 
    def locationPoints(self):
        startX,startY,endX,endY = self.protectRadius()
        points = []
        for i in range(startX,endX):
            for j in range(startY,endY):
                points.append([i,j])
        return points

    def energyNeededToMoveToCharger(self):
        if self.targetCharger==None:
            return 0
        p1 = self.location
        p2 = self.targetCharger.location
        distance = math.sqrt( ((p1[0]-p2[0])**2)+((p1[1]-p2[1])**2) )
        energyRequired = distance* self.energy
        return energyRequired


    def __str__ (self):
        return f"id:{self.id},battery:{self.battery},status:{self.state},location:({self.location})"

class Charger (Component):
    """
        The charger class represnets a charging slot.
        Location: type of a Point (x,y) in a given world.
        Client: a variable to indicate which drone has reserved the time of this charger.
        Rate: the speed (rate) of charging, is basically power unit  / time unit
        Static Count for the Chargers
    """
    # static Counter
    Count = 0

    
    def __init__ (
                    self,
                    location):
                
        Charger.Count = Charger.Count + 1
        Component.__init__(self,location,Charger.Count)
        self.rate = 0.02
    
    def charge(self,drone):
        drone.battery = drone.battery + self.rate

    def __str__ (self):
        return f"{self.id},{self.location}"
  


class BirdState(Enum):
    """
        An enumerate property for the birds.
        IDLE: a default state for birds, when they are out of fields.
        ATTACKING: a state where a bird has a field in mind, and attacking it.
        FLEEING: a state where a bird is running away from drones
    """

    IDLE = 0
    MOVING = 1
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
                    speed=1):

        Bird.Count = Bird.Count + 1
        Agent.__init__(self,location,speed,Bird.Count)

        #self.location = location

        self.state = BirdState.IDLE
        self.target = None
        self.field = None

    def findRandomField(self):
        self.target = Point.random()

    def actuate(self):
        if self.state == BirdState.IDLE:
            probability = random()
            # bird moves if we crossed threshold of StayProbability randomly
            if probability > Bird.StayProbability:
                probability -= Bird.StayProbability
                # to decide wether attack a farm or just move to another place
                if probability < Bird.AttackProbability:
                    self.moveToNewField()
                else:
                    self.moveToNoField()
                self.state = BirdState.MOVING
        
        if self.state == BirdState.MOVING:
            if self.location == self.target:
                self.state = BirdState.OBSERVING
            else:
                self.move (self.target)
        
        if self.state == BirdState.OBSERVING:
            components = Component.World.components(self.location)
            if any ([isinstance(component,Drone) for component in components]):
                self.state = BirdState.FLEEING
            else:
                if any ([isinstance(component,Field) for component in components]):
                    # select a field
                    self.field = [component for component in components if isinstance(component,Field)][0]
                    self.state = BirdState.EATING
                else:
                    self.state = BirdState.IDLE
        
        if self.state == BirdState.EATING:
            components = Component.World.components(self.location)
            if any ([isinstance(component,Drone) for component in components]):
                self.state = BirdState.FLEEING
            else:
                probability = random()
                if probability > Bird.StayProbability:
                    probability -= Bird.StayProbability
                    if probability < Bird.AttackProbability:
                        self.moveWithinSameField()
                    else:
                        self.moveToNoField()
                    self.state = BirdState.MOVING

                else:
                    self.state = BirdState.EATING
        
        if self.state == BirdState.FLEEING:
            self.moveWithinSameField()
            self.state = BirdState.MOVING
        
    
    def moveToNewField(self):
        components = Component.World.map
        fields = [component for component in components if isinstance(component, Field)]
        #random choice
        self.field = choice(fields)
        target = choice(components[self.field ])
        self.target = Point(target[0],target[1])

    def moveToNoField(self):
        self.field = None
        self.target = None
        components = Component.World.map
        fieldsAndDrones = [component for component in components if isinstance(component, Field) or isinstance(component, Drone) ]
        while not isinstance(self.target,Point):
            randomPoint = [randint(0, Component.World.Width-1) , randint(1, Component.World.Height-1)]
            if randomPoint not in fieldsAndDrones:
                self.target = Point(randomPoint[0],randomPoint[1])

    def moveWithinSameField(self):
        if self.field==None:
            self.moveToNewField()
        fieldPoints = Component.World.map[self.field]
        target = choice(fieldPoints)
        self.target = Point(target[0],target[1])
        
    
    def __str__ (self):
        return f"{self.id},{self.state},{self.location}"
