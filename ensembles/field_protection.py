"""
Field protection ensembles
"""
from typing import List

from simulation.components import Field
from simulation.drone import DroneState
from simulation.ensemble import Ensemble, someOf
from utils.verbose import verbosePrint


def getEnsembles(WORLD):

    Drone = WORLD.Drone

    class FieldProtection(Ensemble):

        field: Field

        def __init__(self, field):
            self.field = field
            # stateless ensemble

        drones: List[Drone] = someOf(Drone)

        def priority(self):
            if len(self.field.protectingDrones) == 0:
                return len(self.field.places)
            # if there is no drone assigned, it tries to assign at least one
            return len(self.field.places) / len(self.field.protectingDrones)

        @drones.cardinality
        def drones(self):
            return 1, len(self.field.places)

        # choose this if not selected
        @drones.select
        def drones(self, drone, otherEnsembles):
            return not any(ens for ens in otherEnsembles if isinstance(ens, FieldProtection) and drone in ens.drones) and \
                   drone.state == DroneState.IDLE and \
                   len(self.field.places) > len(self.field.protectingDrones)

        @drones.priority
        def drones(self, drone):
            return - self.field.closestDistanceToDrone(drone)

        def actuate(self):

            for drone in self.drones:
                verbosePrint(f"Protecting Ensemble: assigning {drone.id} to {self.field.id}", 4)
                drone.targetField = self.field

    ensembles = [FieldProtection(field) for field in WORLD.fields]

    return ensembles
