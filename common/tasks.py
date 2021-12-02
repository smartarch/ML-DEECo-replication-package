from common.components import Drone, Field, Charger, DroneState
from common.ensemble import Ensemble, someOf, oneOf
from common.estimator import TimeEstimator
from typing import List

class FieldProtection(Ensemble):
    field: Field

    def __init__(self, field):
        self.field = field
        # stateless ensemble

    drones: List[Drone] = someOf(Drone)

    def priority(self):
        # if there is no drone assigned, it tries to assign at least one
        return len(self.field.protectingDrones)

    @drones.cardinality
    def drones(self):
        return len(self.field.places)

    # choose this if not selected
    @drones.select
    def drones(self, drone, otherEnsembles):
        conditions = [
            not any(ens for ens in otherEnsembles if isinstance(ens, FieldProtection) and drone in ens.drones),
            drone.state == DroneState.IDLE, # drones that are ready to protect
            len(self.field.places) > len(self.field.protectingDrones) # do not assign too many drones
        ]
        return all(conditions)


    @drones.priority
    def drones(self, drone):
        return - self.field.closestDistanceToDrone(drone)

    def actuate(self,verbose):

        for drone in self.drones:
            # only for printing
            if verbose > 3:
                print (f"            Protecting Ensemble: assigning {drone.id} to {self.field.id}")
            drone.targetField= self.field
            
class DroneCharger(Ensemble):
    charger: Charger

    def __init__(self, charger):
        self.charger = charger
        # stateless ensemble

    drone: Drone = oneOf(Drone)

    def priority(self):
        return len(self.charger.chargingDrones)

    @drone.select
    def drone(self, drone, otherEnsembles):
        conditions =[
             drone.needsCharging(), # checks if the drone is dead or alive, and if needs charging
             self.charger == drone.closestCharger(), # if this is the closest charger
             not any(ens for ens in otherEnsembles if isinstance(ens, DroneCharger) and drone == ens.drone),
             drone not in self.charger.chargingQueue, # if the drone is not already chargingQueue (simplified)
             drone not in self.charger.chargingDrones, # if the drone is not already being charged (can be asked in drone.needsCharging() too.)
        ]
        return all(conditions)

    @drone.priority
    def drone(self, drone):
        return drone.location.distance(self.charger.location)

    def actuate(self,verbose):
        # only for printing
        if verbose > 3:
            print (f"            Charging Ensemble: assigned {self.drone.id} to {self.charger.id}")

        self.charger.addToQueue(self.drone)


def getPotentialEnsembles(world):
    potentialEnsembles = []
    for field in world.fields:
        potentialEnsembles.append(FieldProtection(field))
    
    for charger in world.chargers:
        potentialEnsembles.append(DroneCharger(charger))
    
    return potentialEnsembles


