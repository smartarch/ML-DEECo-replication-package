from common.components import Drone, Field, Charger,DroneState
from common.ensemble import Ensemble, someOf, oneOf
from typing import List

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
        return len(self.field.places) 

    def actuate(self):
        for (drone,place) in zip(self.drones,self.field.randomPlaces(len(self.drones))):
            drone.targetFieldPosition = place

class PrivateChargerAssignment(Ensemble):
    drone: Drone

    def __init__(self, drone):
        self.drone = drone

    def needsCharging(self):
        return self.drone.criticalBattery()

    # check the distance to the charger
    def distanceToCharger(self, charger):
        return self.drone.location.distance(charger.location)

    charger: Charger = oneOf(Charger)

    @charger.select
    def charger(self, charger, otherEnsembles):
        return True

    @charger.priority
    def charger(self, charger):
        return -self.distanceToCharger(charger)

    def actuate(self):
        if self.drone in self.charger.acceptedDrones:
            return
        if self.drone not in self.charger.waitingDrones:
            self.charger.waitingDrones.append(self.drone)
            self.drone.targetCharger = self.charger