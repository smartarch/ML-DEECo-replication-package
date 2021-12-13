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
        return all([
            not any(ens for ens in otherEnsembles if isinstance(ens, FieldProtection) and drone in ens.drones),
            drone.state == DroneState.IDLE,  # drones that are ready to protect
            len(self.field.places) > len(self.field.protectingDrones)  # do not assign too many drones
        ])

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
        return all([
            #drone.needsCharging(),  # checks if the drone is dead or alive, and if needs charging
            drone in self.charger.potentialDrones,  #drone.closestCharger(),  # if this is the closest charger
            not any(ens for ens in otherEnsembles if isinstance(ens, DroneCharger) and drone == ens.drone),
            drone not in self.charger.chargingQueue,  # if the drone is not already chargingQueue (simplified)
            drone not in self.charger.chargingDrones,  # if the drone is not already being charged (can be asked in drone.needsCharging() too.)
        ])

    @drone.priority
    def drone(self, drone):
        return drone.location.distance(self.charger.location)

    def actuate(self, verbose):
        # only for printing
        if verbose > 3:
            print(f"            Charging Ensemble: assigned {self.drone.id} to {self.charger.id}")

        # TODO: MT, the charger decides for the drone
        # Step 0: (Done on the drone side), the drone is added to Charger's Potential List
        # Step 1: Add the drone to the waiting list (drone will keep protecting)
        # Step 2: Set drone's Target Charger (drone will move toward the charger)
        # Step 3: If drone arrived to the charger, it will remove it from waiting list and add
        # it to the charging drones
        # Step 4: when drone is done charging, the Target Charger will be None and
        # it will be removed from charging list
        self.charger.decide(self.drone)


class ChargerFinder(Ensemble):
    drone: Drone

    def __init__(self, drone):
        self.drone = drone
        # stateless ensemble

    charger: Charger = oneOf(Charger)

    def priority(self):
        return - self.drone.battery

    # @chargers.cardinality
    # def chargers(self):
    #     return 2    # find top two closest chargers 

    # choose this if not selected
    @charger.select
    def charger(self, charger, otherEnsembles):
        return self.drone not in charger.potentialDrones #and charger not in self.chargers

    @charger.priority
    def charger(self, charger):
        return -self.drone.location.distance(charger.location)

    def actuate(self, verbose):

        closestCharger = self.charger
        if self.drone.closestCharger is not None:
            self.drone.closestCharger.potentialDrones.remove(self.drone)
        
        self.drone.closestCharger = closestCharger
        closestCharger.potentialDrones.append(self.drone)
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
