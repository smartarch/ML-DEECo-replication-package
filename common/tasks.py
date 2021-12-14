from common.components import Drone, Field, Charger, DroneState
from common.ensemble import Ensemble, someOf, oneOf
from typing import List


####################
# Field protection #
####################


class FieldProtection(Ensemble):
    field: Field

    def __init__(self, field):
        self.field = field
        # stateless ensemble

    drones: List[Drone] = someOf(Drone)

    def priority(self):
        if len(self.field.protectingDrones) == 0:
            return 1 / len(self.field.places)
        # if there is no drone assigned, it tries to assign at least one
        return len(self.field.protectingDrones) / len(self.field.places)

    @drones.cardinality
    def drones(self):
        return len(self.field.places)

    # choose this if not selected
    @drones.select
    def drones(self, drone, otherEnsembles):
        return not any(ens for ens in otherEnsembles if isinstance(ens, FieldProtection) and drone in ens.drones) and \
               drone.state == DroneState.IDLE and \
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


##################
# Drone charging #
##################
# Step 0: (ChargerFinder) The drone is added to Charger's Potential list.
# Step 1: (DroneCharger) Add the drone to the waiting list (drone will keep protecting).
# Step 2: Set drone's Target Charger (drone will move toward the charger).
# Step 3: If drone arrived to the charger, it will remove it from waiting list and add it to the charging drones.
# Step 4: When drone is done charging, the Target Charger will be None and it will be removed from charging list.


class DroneCharger(Ensemble):
    charger: Charger

    def __init__(self, charger):
        self.charger = charger
        # stateless ensemble

    drones: List[Drone] = someOf(Drone)

    @drones.cardinality
    def drones(self):
        return 1, len(self.charger.potentialDrones)

    def priority(self):
        return len(self.charger.chargingDrones)

    @drones.select
    def drones(self, drone, otherEnsembles):
        return drone.state != DroneState.TERMINATED and \
               drone in self.charger.potentialDrones and \
               drone.needsCharging() and \
               drone not in self.drones and \
               drone not in self.charger.chargingQueue and \
               drone not in self.charger.chargingDrones

        # not any(ens for ens in otherEnsembles if isinstance(ens, DroneCharger) and drone == ens.drone) and\
        # return drone.state != DroneState.TERMINATED and\
        #     drone in self.charger.potentialDrones and\
        #     not any(ens for ens in otherEnsembles if isinstance(ens, DroneCharger) and drone == ens.drone) and\
        #     drone not in self.charger.chargingQueue and\
        #     drone not in self.charger.chargingDrones  # if the drone is not already being charged (can be asked in drone.needsCharging() too.)

    @drones.priority
    def drones(self, drone):
        return drone.batteryAfterGetToCharger(self.charger)

    def actuate(self, verbose):

        # only for printing
        if verbose > 3:
            print(f"            Charging Ensemble: assigned {len(self.drones)} to {self.charger.id}")

        for drone in self.drones:
            self.charger.addToQueue(drone)


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
        return True

    @charger.priority
    def charger(self, charger):
        return -self.drone.location.distance(charger.location)

    def actuate(self, verbose):

        if self.drone.closestCharger is not None:
            try:
                self.drone.closestCharger.potentialDrones.remove(self.drone)
            except ValueError:
                pass

        if self.drone.state == DroneState.TERMINATED:
            self.charger.droneDied(self.drone)
            self.drone.closestCharger = None
            return

        if self.drone in self.charger.chargingDrones + self.charger.chargingQueue:
            return

        closestCharger = self.charger
        self.drone.closestCharger = closestCharger
        closestCharger.potentialDrones.append(self.drone)
        if verbose > 3:
            print(f"            Charger Finder: adding {self.drone.id} to {closestCharger.id}")


#######################
# Potential ensembles #
#######################


def getPotentialEnsembles(world):
    potentialEnsembles = []
    for field in world.fields:
        potentialEnsembles.append(FieldProtection(field))

    for charger in world.chargers:
        potentialEnsembles.append(DroneCharger(charger))

    for drone in world.drones:
        potentialEnsembles.append(ChargerFinder(drone))

    return potentialEnsembles
