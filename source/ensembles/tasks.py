from typing import List

from source.ensembles.ensemble import Ensemble, oneOf, someOf
from source.components.bird import Bird
from source.components.drone import DroneState,Drone
from source.components.point import Point
from source.components.field import Field
from source.components.charger import Charger

import random

# a new ensemble to give 


class FieldProtection(Ensemble):
    field: Field

    def __init__(self, field):
        self.field = field

    def distanceToField(self, drone):
        # TODO
        return 1
    drones: List[Drone] = someOf(Drone)

    @drones.cardinality
    def drones(self):
        return len(self.field.places)

    # choose this if not selected
    @drones.select
    def drones(self, drone, otherEnsembles):
        return drone.state == DroneState.IDLE and not any(ens for ens in otherEnsembles if isinstance(ens, FieldProtection) and drone in ens.drones)

    @drones.priority
    def drones(self, drone):
        return -self.distanceToField(drone)

    def actuate(self):
        for drone in self.drones:
            drone.targetFieldPosition = random.choice(self.field.places)
