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
            return len(self.field.places)
        # if there is no drone assigned, it tries to assign at least one
        return len(self.field.places) / len(self.field.protectingDrones)

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
# Step 4: When drone is done charging, the Target Charger will be None, and it will be removed from charging list.


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
        return 1

    @drones.select
    def drones(self, drone, otherEnsembles):
        return drone.state != DroneState.TERMINATED and \
               drone in self.charger.potentialDrones and \
               drone.needsCharging() and \
               drone not in self.drones and \
               drone not in self.charger.waitingDrones and \
               drone not in self.charger.chargingDrones

        # not any(ens for ens in otherEnsembles if isinstance(ens, DroneCharger) and drone == ens.drone) and\
        # return drone.state != DroneState.TERMINATED and\
        #     drone in self.charger.potentialDrones and\
        #     not any(ens for ens in otherEnsembles if isinstance(ens, DroneCharger) and drone == ens.drone) and\
        #     drone not in self.charger.chargingQueue and\
        #     drone not in self.charger.chargingDrones  # if the drone is not already being charged (can be asked in drone.needsCharging() too.)

    @drones.priority
    def drones(self, drone):
        return -drone.timeToDoneCharging()

    def actuate(self, verbose):

        # only for printing
        if verbose > 3:
            print(f"            Charging Ensemble: assigned {len(self.drones)} to {self.charger.id}")


            """
                chargerLog = Log([
                        "drone_id",
                        "battery",
                        "future_battery",
                        "estimated_waiting",
                        "energy_needed_to_charge",
                        "time_to_charge",
                        "charger",
                        "potential_drones_length",
                        "waiting_drones_length",
                        "accepted_queues_length",
                        "charging_drones_length"

                    ])
            """
        for drone in self.drones:
            self.charger.world.chargerLog.register([
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
            self.charger.addToQueue(drone)
            


class DroneChargerPriority(Ensemble):
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
               drone.needsCharging() and \
               drone not in self.drones and \
               drone not in self.charger.waitingDrones and \
               drone not in self.charger.chargingDrones
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

        for drone in self.drones:
            self.charger.addToQueue(drone)  # we add the drone to the waiting queue, it should be immediately moved to the acceptedDrones by the charger


class ChargerFinder(Ensemble):
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
               not any(ens for ens in otherEnsembles if isinstance(ens, ChargerFinder) and drone in ens.drones) and \
               drone not in self.drones and \
               not drone.isChargingOrWaiting() and \
               drone.findClosestCharger() == self.charger

        # not any(ens for ens in otherEnsembles if isinstance(ens, DroneCharger) and drone == ens.drone) and\
        # return drone.state != DroneState.TERMINATED and\
        #     drone in self.charger.potentialDrones and\
        #     not any(ens for ens in otherEnsembles if isinstance(ens, DroneCharger) and drone == ens.drone) and\
        #     drone not in self.charger.chargingQueue and\
        #     drone not in self.charger.chargingDrones  # if the drone is not already being charged (can be asked in drone.needsCharging() too.)

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


# class ChargerFinder(Ensemble):

#     drone: Drone

#     def __init__(self, drone):
#         self.drone = drone

#     def priority(self):
#         return 2  # It is necessary to run this before DroneCharger. The order of ChargerFinder ensembles can be arbitrary as they don't influence each other.

#     # TODO: we could add something like this to make a "select" for the ensemble itself
#     # def select(self):
#     #     return self.drone.state != DroneState.TERMINATED

#     charger: Charger = oneOf(Charger)

#     @charger.select
#     def charger(self, charger, otherEnsembles):
#         return True

#     @charger.priority
#     def charger(self, charger):
#         return -self.drone.location.distance(charger.location)

#     # TODO: go through this and think about it again
#     # we could just empty the potentialDrones in each time step and construct them from scratch instead of adding and removing drones
#     # def actuate(self, verbose):

#     #     if self.drone.closestCharger is not None:
#     #         try:
#     #             self.drone.closestCharger.potentialDrones.remove(self.drone)
#     #         except ValueError:
#     #             pass

#     #     if self.drone.state == DroneState.TERMINATED:
#     #         self.charger.droneDied(self.drone)  # TODO: should we notify `self.charger` charger or `self.drone.closestCharger`?
#     #         self.drone.closestCharger = None
#     #         return
#     #     self.drone.newClosestCharger(self.charger)
#     #     # if self.drone.closestCharger is not None and \
#     #     #         self.drone in self.drone.closestCharger.chargingDrones + self.drone.closestCharger.chargingQueue:
#     #     #     return

#     #     # closestCharger = self.charger
#     #     # self.drone.closestCharger = closestCharger
#     #     self.drone.closestCharger.potentialDrones.append(self.drone)
#     #     if verbose > 3:
#     #         print(f"            Charger Finder: adding {self.drone.id} to {closestCharger.id}")


#######################
# Potential ensembles #
#######################


def getPotentialEnsembles(world, queue_type):
    potentialEnsembles = []
    for field in world.fields:
        potentialEnsembles.append(FieldProtection(field))

    for charger in world.chargers:
        if queue_type == "fifo":
            potentialEnsembles.append(DroneCharger(charger))
        elif queue_type == "priority":
            potentialEnsembles.append(DroneChargerPriority(charger))
        potentialEnsembles.append(ChargerFinder(charger))

    return potentialEnsembles
