"""
Field protection ensembles
"""
from typing import List, TYPE_CHECKING
from simulation.world import ENVIRONMENT, WORLD
from simulation.drone_state import DroneState
from simulation.ensemble import Ensemble, someOf,oneOf
from utils.verbose import verbosePrint
from simulation.drone import Drone

if TYPE_CHECKING:
    from simulation.components import Field


class FieldProtection(Ensemble):

    field: 'Field'

    def __init__(self, field: 'Field'):
        self.field = field

    drone: Drone = oneOf(Drone)

    def priority(self):
        if len(self.field.protectingDrones) == 0:
            return -len(self.field.places)
        # if there is no drone assigned, it tries to assign at least one
        #return len(self.field.places) / len(self.field.protectingDrones)
        return -1*(len(self.field.places) - len(self.field.protectingDrones))

    # @drones.cardinality
    # def drones(self):
    #     return 1, len(self.field.places)

    # choose this if not selected
    @drone.select
    def drone(self, drone, otherEnsembles):
        #return not any(ens for ens in otherEnsembles if isinstance(ens, FieldProtection) and drone in ens.drones) and \
        return drone.state == DroneState.IDLE and \
               len(self.field.places) > len(self.field.protectingDrones)

    @drone.priority
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
