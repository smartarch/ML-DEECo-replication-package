from source.components.agent import Agent
from source.components.component import Component
from source.components.field import Field
from source.components.point import Point
from source.components.drone import Drone
from enum import Enum
import random

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
            probability = random.random()
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
                probability = random.random()
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
        self.field = random.choice(fields)
        target = random.choice(components[self.field ])
        self.target = Point(target[0],target[1])

    def moveToNoField(self):
        self.field = None
        self.target = None
        components = Component.World.map
        fieldsAndDrones = [component for component in components if isinstance(component, Field) or isinstance(component, Drone) ]
        while not isinstance(self.target,Point):
            randomPoint = [random.randint(0, Component.World.Width-1) ,random.randint(1, Component.World.Height-1)]
            if randomPoint not in fieldsAndDrones:
                self.target = Point(randomPoint[0],randomPoint[1])

    def moveWithinSameField(self):
        if self.field==None:
            self.moveToNewField()
        fieldPoints = Component.World.map[self.field]
        target = random.choice(fieldPoints)
        self.target = Point(target[0],target[1])
        
    
    def __str__ (self):
        return f"{self.id},{self.state},{self.location}"