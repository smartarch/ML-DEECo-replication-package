from simulation.components import Drone, Field, Charger, DroneState
from simulation.ensemble import Ensemble, someOf
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
            return len(self.field.places)
        # if there is no drone assigned, it tries to assign at least one
        return len(self.field.places) / len(self.field.protectingDrones)

    @drones.cardinality
    def drones(self):
        return (1,len(self.field.places))

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
# Step 4: When drone is done charging, the Target Charger will be None, and it will be removed from charging list.


class WaitingDronesAssignment(Ensemble):
    charger: Charger

    def __init__(self, charger):
        self.charger = charger
        # stateless ensemble

    drones: List[Drone] = someOf(Drone)

    @drones.cardinality
    def drones(self):
        return 1, len(self.charger.potentialDrones)

    def priority(self):
        return 1

    @drones.select
    def drones(self, drone, otherEnsembles):
        return drone.state != DroneState.TERMINATED and \
               drone in self.charger.potentialDrones and \
               drone.needsCharging()

    @drones.priority
    def drones(self, drone):
        return -drone.timeToDoneCharging()

    def actuate(self, verbose):

        # only for printing
        if verbose > 3:
            print(f"            Charging Ensemble: assigned {len(self.drones)} to {self.charger.id}")

        # Do the logging first, then add the drones to the queue (otherwise the queue length is incorrect).
        for drone in self.drones:
            self.charger.world.chargerLog.register([
                drone.world.currentTimeStep,
                drone.id,
                drone.battery,
                drone.computeFutureBattery(),
                drone.estimateWaitingEnergy(drone.closestCharger),
                drone.energyRequiredToGetToCharger(drone.closestCharger.location),
                drone.timeToDoneCharging(),
                self.charger.id,
                len(self.charger.potentialDrones),
                len(self.charger.waitingDrones),
                len(self.charger.acceptedDrones),
                len(self.charger.chargingDrones),
            ])
        for drone in self.drones:
            self.charger.addToQueue(drone)


class AcceptedDronesAssignment(Ensemble):
    charger: Charger

    def __init__(self, charger):
        self.charger = charger

    drones: List[Drone] = someOf(Drone)

    @drones.cardinality
    def drones(self):
        return 1, self.charger.acceptedCapacity - len(self.charger.acceptedDrones)  # free slots in the acceptedDrones

    def priority(self):
        return 1

    @drones.select
    def drones(self, drone, otherEnsembles):
        cond = drone.state != DroneState.TERMINATED and \
               drone in self.charger.potentialDrones and \
               drone.needsCharging()
               # TODO(MT): or self.charger.acceptedDrones
        if cond:
            # TODO(MT): move the estimator to the ensemble
            self.charger.waitingTimeEstimator.collectRecordStart(drone.id, self.charger, drone, self.charger.world.currentTimeStep)
        return cond

    @drones.priority
    def drones(self, drone):
        return -drone.timeToDoneCharging()

    def actuate(self, verbose):

        # only for printing
        if verbose > 3:
            print(f"            Charging Ensemble: assigned {len(self.drones)} to {self.charger.id}")

        # TODO(MT): set the acceptedDrones by the ensemble, don't manage it in the charger
        for drone in self.drones:
            self.charger.acceptForCharging(drone)


class PotentialDronesAssignment(Ensemble):

    charger: Charger

    def __init__(self, charger):
        self.charger = charger
        # stateless ensemble

    drones: List[Drone] = someOf(Drone)

    @drones.cardinality
    def drones(self):
        return 0, len(self.charger.world.drones)

    def priority(self):
        return 2  # It is necessary to run this before DroneCharger. The order of ChargerFinder ensembles can be arbitrary as they don't influence each other.

    @drones.select
    def drones(self, drone, otherEnsembles):
        return drone.state != DroneState.TERMINATED and \
               not any(ens for ens in otherEnsembles if isinstance(ens, PotentialDronesAssignment) and drone in ens.drones) and \
               drone not in self.drones and \
               not drone.isChargingOrWaiting() and \
               drone.findClosestCharger() == self.charger

    @drones.priority
    def drones(self, drone):
        return -drone.location.distance(self.charger.location)

    def actuate(self, verbose):

        # only for printing
        self.charger.potentialDrones = self.drones
        for drone in self.drones:
            drone.closestCharger = self.charger
        
        if verbose > 3:
            print(f"            Charger Finder: assigned {len(self.drones)} to {self.charger.id}")


#######################
# Potential ensembles #
#######################


def getPotentialEnsembles(world, queue_type):
    potentialEnsembles = []
    for field in world.fields:
        potentialEnsembles.append(FieldProtection(field))

    for charger in world.chargers:
        if queue_type == "fifo":
            potentialEnsembles.append(WaitingDronesAssignment(charger))
        elif queue_type == "priority":
            potentialEnsembles.append(AcceptedDronesAssignment(charger))
        potentialEnsembles.append(PotentialDronesAssignment(charger))

    return potentialEnsembles
