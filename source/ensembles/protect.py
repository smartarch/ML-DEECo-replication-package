from typing import List

from source.ensembles.ensemble import Ensemble, oneOf, someOf
from source.components.bird import Bird
from source.components.drone import DroneState,Drone
from source.components.point import Point
from source.components.field import Field
from source.components.charger import Charger
import random
import math

class FieldProtection(Ensemble):
    field: Field

    def __init__(self, field):
        self.field = field
        self.extraDrones = 0

    def assignCardinality (self, extraDrones):
        self.extraDrones = self.extraDrones + extraDrones
        
    def distanceToField(self, drone):
        return self.field.closestDistanceToDrone(drone) 

    drones: List[Drone] = someOf(Drone)

    @drones.cardinality
    def drones(self):
        #return len(self.field.zones)
        return self.extraDrones + 1

    # choose this if not selected
    @drones.select
    def drones(self, drone, otherEnsembles):
        return (drone.state == DroneState.IDLE) and (not any(ens for ens in otherEnsembles if isinstance(ens, FieldProtection) and drone in ens.drones)) and drone not in self.drones

    @drones.priority
    def drones(self, drone):
        return - self.distanceToField (drone) 

    def size (self):
        return len(self.field.zones) 

    def actuate(self):
        for (drone,place) in zip(self.drones,self.field.randomZones(len(self.drones))):
            drone.targetFieldPosition = place