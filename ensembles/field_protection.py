"""
Field protection ensembles
"""
from typing import List, TYPE_CHECKING

from simulation.drone_state import DroneState
from simulation.ensemble import Ensemble, someOf
from utils.verbose import verbosePrint
from simulation.drone import Drone

if TYPE_CHECKING:
    from simulation.components import Field


class FieldProtection(Ensemble):

    field: 'Field'

    def __init__(self, field: 'Field'):
        self.field = field

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


def getEnsembles(world):

    ensembles = [FieldProtection(field) for field in world.fields]

    return ensembles
