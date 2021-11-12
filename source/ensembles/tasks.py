from typing import List

from source.ensembles.ensemble import Ensemble, oneOf, someOf
from source.components.bird import Bird
from source.components.drone import DroneState,Drone
from source.components.point import Point
from source.components.field import Field
from source.components.charger import Charger

import random

# a new ensemble to give 

class ChargerAssignment(Ensemble):
    charger: Charger

    def __init__(self, charger):
        self.charger = charger

    def needsCharging(self, drone):
        return True

    # check the distance to the charger
    def energyNeededToStartCharging(self, drone):
        return 0.1

    drone: Drone = oneOf(Drone)

    @drone.select
    def drone(self, drone, otherEnsembles):
        return not any(ens for ens in otherEnsembles if isinstance(ens, ChargerAssignment) and ens.drone == drone) and self.needsCharging(drone)

    @drone.priority
    def drone(self, drone):
        return self.energyNeededToStartCharging(drone) - drone.battery

    # tells the drone this is your charger
    def actuate(self):
        self.drone.targetCharger = self.charger


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
