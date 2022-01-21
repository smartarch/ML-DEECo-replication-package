import random
from enum import Enum

from world import ENVIRONMENT, WORLD
from ml_deeco.simulation import Agent


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
    TimeToEat = 5
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

    def moveToNewField(self):
        self.field = random.choice(WORLD.fields)
        newTarget = self.field.randomUndamagedCorp()
        if newTarget is None:
            self.field = None
            self.state = BirdState.IDLE
        else:
            self.target = newTarget
            self.state = BirdState.MOVING_TO_FIELD

    def moveToNoField(self):
        self.field = None
        self.target = random.choice(WORLD.emptyPoints)
        self.state = BirdState.FLEEING

    def moveWithinSameField(self):
        if self.field == None:
            self.moveToNewField()
        else:
            newTarget = self.field.randomUndamagedCorp()
            if newTarget is None:
                self.field = None
                self.state = BirdState.IDLE
            else:
                self.target = newTarget
                self.state = BirdState.MOVING_TO_FIELD

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
            self.ate = self.ate
            self.field.locationDamaged(self.location)
            probability = random.random()
            if probability > Bird.StayProbability:
                probability -= Bird.StayProbability
                if probability < Bird.AttackProbability:
                    self.moveWithinSameField()
                else:
                    self.moveToNoField()
                    self.state = BirdState.FLEEING
            else:
                self.moveWithinSameField()



    def __repr__(self):
        return f"{self.id}: state={self.state}, Total Ate={self.ate}"