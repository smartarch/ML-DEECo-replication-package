from source.components.agent import Agent
from source.components.component import Component
from source.components.field import Field
from source.components.point import Point
from source.components.drone import Drone
from source.components.states import BirdState
import random


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
        Agent.__init__(self,location,self.speed,world,Bird.Count)

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
            components = self.world.components(self.location)
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
            components = self.world.components(self.location)
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
            self.moveToNoField()
            self.state = BirdState.MOVING
        
    
    def moveToNewField(self):
        components = self.world.map
        fields = [component for component in components if isinstance(component, Field)]
        #random choice
        self.field = random.choice(fields)
        target = random.choice(components[self.field ])
        self.target = Point(target[0],target[1])

    def moveToNoField(self):
        self.field = None
        self.target = None
        components = self.world.map
        fieldsAndDrones = [component for component in components if isinstance(component, Field) or isinstance(component, Drone) ]
        while not isinstance(self.target,Point):
            randomPoint = [random.randint(0, self.world.mapWidth-1) ,random.randint(1, self.world.mapHeight-1)]
            if randomPoint not in fieldsAndDrones:
                self.target = Point(randomPoint[0],randomPoint[1])

    def moveWithinSameField(self):
        if self.field==None:
            self.moveToNewField()
        fieldPoints = self.world.map[self.field]
        target = random.choice(fieldPoints)
        self.target = Point(target[0],target[1])
        
    
    def __str__ (self):
        return f"{self.id},{self.state},{self.location}"