"""
Field protection ensembles
"""
from typing import TYPE_CHECKING

from world import WORLD
from components.drone_state import DroneState
from components.drone import Drone

from ml_deeco.simulation import Ensemble, oneOf
from ml_deeco.utils import verbosePrint

if TYPE_CHECKING:
    from components.field import Field


class FieldProtection(Ensemble):

    field: 'Field'

    def __init__(self, field: 'Field'):
        self.field = field

    drone: Drone = oneOf(Drone)

    def priority(self):
        if len(self.field.protectingDrones) == 0:
            return -len(self.field.places)
        # if there is no drone assigned, it tries to assign at least one
        # return len(self.field.places) / len(self.field.protectingDrones)
        return len(self.field.protectingDrones) / len(self.field.places)

    # @drones.cardinality
    # def drones(self):
    #     return 1, len(self.field.places)

    # choose this if not selected
    @drone.select
    def drone(self, drone, otherEnsembles):
        # return not any(ens for ens in otherEnsembles if isinstance(ens, FieldProtection) and drone in ens.drones) and \
        return drone.state == DroneState.IDLE and \
               len(self.field.places) > len(self.field.protectingDrones)

    @drone.utility
    def drones(self, drone):
        return - self.field.closestDistanceToDrone(drone)

    def actuate(self):
        self.drone.targetField = self.field
        verbosePrint(f"Protecting Ensemble: assigning {self.drone.id} to {self.field.id}", 4)
        # for drone in self.drones:
        #     
        #     drone.targetField = self.field


def getEnsembles():
    ensembles = [FieldProtection(field) for field in WORLD.fields]
    return ensembles