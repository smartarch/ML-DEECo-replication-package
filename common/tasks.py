from common.components import Drone, Field, Charger, DroneState
from common.ensemble import Ensemble, someOf, oneOf
from typing import List


class FieldProtection(Ensemble):
    field: Field

    def __init__(self, field):
        self.field = field
        # stateless ensemble

    drones: List[Drone] = someOf(Drone)

    def priority(self):
        if len(self.field.protectingDrones) ==0:
            return 1/len(self.field.places)
        # if there is no drone assigned, it tries to assign at least one
        return len(self.field.protectingDrones) / len(self.field.places)

    @drones.cardinality
    def drones(self):
        return len(self.field.places)

    # choose this if not selected
    @drones.select
    def drones(self, drone, otherEnsembles):
        return  not any(ens for ens in otherEnsembles if isinstance(ens, FieldProtection) and drone in ens.drones) and\
            drone.state == DroneState.IDLE and\
            len(self.field.places) > len(self.field.protectingDrones)

    @drones.priority
    def drones(self, drone):
        return - self.field.closestDistanceToDrone(drone)

    def actuate(self, verbose):

        for drone in self.drones:
            # only for printing
            if verbose > 3:
                print(f"            Protecting Ensemble: assigning {drone.id} to {self.field.id}")
            drone.targetField = self.field


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
        #drone.closestCharger(),  # if this is the closest charger
        # if the drone is not already chargingQueue (simplified)
        # if the drone is not already being charged (can be asked in drone.needsCharging() too.)
        return  drone in self.charger.potentialDrones and\
            drone not in self.charger.chargingQueue and\
            drone not in self.charger.chargingDrones and\
            not any(ens for ens in otherEnsembles if isinstance(ens, DroneCharger) and drone == ens.drone) and\
            drone.needsCharging()

    @drone.priority
    def drone(self, drone):
        return drone.batteryAfterGetToCharger()

    def actuate(self, verbose):
        # the charger decides for the drone
        # Step 0: (Done on the drone side), the drone is added to Charger's Potential List
        # Step 1: Add the drone to the waiting list (drone will keep protecting)
        # Step 2: Set drone's Target Charger (drone will move toward the charger)
        # Step 3: If drone arrived to the charger, it will remove it from waiting list and add
        # it to the charging drones
        # Step 4: when drone is done charging, the Target Charger will be None and
        # it will be removed from charging list
        if self.drone not in self.charger.chargingQueue:
            self.charger.addToQueue(self.drone)
            # only for printing
            if verbose > 3:
                print(f"            Charging Ensemble: assigned {self.drone.id} to {self.charger.id}")

class ChargerFinder(Ensemble):
    drone: Drone

    def __init__(self, drone):
        self.drone = drone
        # stateless ensemble

    charger: Charger = oneOf(Charger)

    def priority(self):
        if self.drone.state==DroneState.TERMINATED:
            return 1
        return - self.drone.battery

    @charger.select
    def charger(self, charger, otherEnsembles):
        return True

    @charger.priority
    def charger(self, charger):
        return -self.drone.location.distance(charger.location)

    def actuate(self, verbose):
        closestCharger = self.charger
        if self.drone.closestCharger is not None:
            if self.drone in self.drone.closestCharger.potentialDrones:
                self.drone.closestCharger.potentialDrones.remove(self.drone)
        
        self.drone.closestCharger = closestCharger
        if self.drone not in self.drone.closestCharger.potentialDrones:
            self.drone.closestCharger.potentialDrones.append(self.drone)   
        if verbose > 3:
            print(f"            Charger Ensemble: adding {self.drone.id} to {closestCharger.id}")
        

def getPotentialEnsembles(world):
    potentialEnsembles = []
    for field in world.fields:
        potentialEnsembles.append(FieldProtection(field))

    for charger in world.chargers:
        potentialEnsembles.append(DroneCharger(charger))

    for drone in world.drones:
        potentialEnsembles.append(ChargerFinder(drone))

    return potentialEnsembles
