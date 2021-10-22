
from .ensemble import Ensemble
from .base import Charger, Drone, Bird

class ChargerAssignment(Ensemble): # This formed only until the drone starts charging
    
    charger: Charger

    def __init__(self, charger):
    	self.charger = charger
    """
    NEEDS CLARIFICATION
    drone: Drone[1]
        not in other Drone.drone
    order lambda drone: drone.battery - drone.energyNeededToStartCharging, order=ASC

    def isMember(
    """
    def selectComponents(self, allComponents, allEnsemblesSoFarInThisRound):
        # select the drones that are already in this Ensemble
        dronesAlreadySelected = [ens.drone for ens in allEnsemblesSoFarInThisRound if isinstance(ens, ChargerAssignment)]

        # select all other drones that are not part of this ensemble
        allDrones = [drone for drone in allComponents if isinstance(drone, Drone) and drone not in dronesAlreadySelected]
        allDrones = sorted(allDrones, key=lambda drone: drone.battery - drone.energyNeededToStartCharging(), order=ASC)
        potentialDrones = [drone for drone in allDrones and drone.needsCharging()]
        if len(potentialDrones) > 0:
            self.drone = potentialDrones[0]
            return True
        else:
            return False

    def actuation(self):
      	self.drone.targetCharger = self.charger
      
    
class FieldProtection(Ensemble):
    def __init__(self, field):
    	self.field = field
    """
        drones: Drone[self.numberOfDronesNeededForProtection(field)]
    
        select drones which are IDLE
        order them by distance to the field
      
    """

    def actuation(self):
      	for drone, pos in zip(self.drones, self.field.places):
      		drone.targetFieldPosition = pos