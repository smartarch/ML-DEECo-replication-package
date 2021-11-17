from source.components.component import Component
from source.components.point import Point
import random
import math

class Agent (Component):
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
    reporter = None
    header = ""
    
    def __init__ (
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
        Component.__init__(self,location,world,count)
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
        dx = target[0] - self.location[0]
        dy = target[1] - self.location[1]
        dl = math.sqrt(dx * dx + dy * dy)
        randomFactor = random.random()+1
        if dl >= self.speed * randomFactor:
            self.location = Point(int(self.location[0] + dx * self.speed * randomFactor / dl),
                                int(self.location[1] + dy * self.speed * randomFactor / dl))
        else:
            self.location = target

    def report(self,timeStep):
        """
            Register the current situation of the agent in the Report object.
            Parameters
            ----------
            timeStep : int
                the current time step the simulation is running in.
        """
        Agent.reporter(self,timeStep)