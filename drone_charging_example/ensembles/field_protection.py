from typing import TYPE_CHECKING
from world import WORLD
from components.drone_state import DroneState
from components.drone import Drone
from ml_deeco.simulation import Ensemble, oneOf
from ml_deeco.utils import verbosePrint
if TYPE_CHECKING:
    from components.field import Field

class FieldProtection(Ensemble):
    """

    The field protection is materialized with one field and one drone.
    THe drone is selected if it is idle, to protect the field.

    Parameters
    ----------
    field : Field
        The field component.

    Properties:
    ---------
    drone: Drone (oneOf) Drones
    """

    field: 'Field'

    def __init__(self, field: 'Field'):
        """
        Initate the ensemble.

        Parameters
        ----------
        field : Field
            The field which needs protection.
        """
        self.field = field

    drone: Drone = oneOf(Drone)

    def priority(self):
        """

        The ensembles are sorted to the priority. 
        If a field has no protectors, it will come as a negative int < 0.
        Otherwise they are sorted to the fact which has less protectors.

        Returns
        -------
        float
            The importance of the field.
        """
        if len(self.field.protectingDrones) == 0:
            return -len(self.field.places)
        # if there is no drone assigned, it tries to assign at least one
        return len(self.field.protectingDrones) / len(self.field.places)

    @drone.select
    def drone(self, drone, otherEnsembles):
        """
    
        Selects the drone to be used for protecting.

        Parameters
        ----------
        drone : Drone
            The drone to be selected.
        otherEnsembles : List
            unused in this concept, but defined by Ensemble definition.

        Returns
        -------
        bool
            if the drone is selected or not.
        """
        # return not any(ens for ens in otherEnsembles if isinstance(ens, FieldProtection) and drone in ens.drones) and \
        return drone.state == DroneState.IDLE and \
               len(self.field.places) > len(self.field.protectingDrones)

    @drone.utility
    def drones(self, drone):
        """

        Utilize the drone list to select the most suitable drone.
        In this case the closest drone will work better.

        Parameters
        ----------
        drone : Drone
            The drone to be selected.

        Returns
        -------
        int
            The distance of the drone to the closest field.
        """
        return - self.field.closestDistanceToDrone(drone)

    def actuate(self):
        """
        Assing selected drone to the field, indirectly.
        Basically, this ensemble tells the drone which field it must protect.
        """
        self.drone.targetField = self.field
        verbosePrint(f"Protecting Ensemble: assigning {self.drone.id} to {self.field.id}", 4)

def getEnsembles():
    """

    Creates a list of ensembles per each field.

    Returns
    -------
    list
        List of field protection ensembles
    """
    ensembles = [FieldProtection(field) for field in WORLD.fields]
    return ensembles
