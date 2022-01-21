import math
import random

from ml_deeco.estimators import Estimate


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

    def __init__(self, x, y):
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

    def __init__(self, location, speed, componentID):
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
        Component.__init__(self, location, componentID)
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
