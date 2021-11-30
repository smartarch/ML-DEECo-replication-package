from common.components import Drone, Field, Charger, DroneState
from common.ensemble import Ensemble, someOf, oneOf
from common.estimator import TimeEstimator
from typing import List
import math


class FieldProtection(Ensemble):
    field: Field

    def __init__(self, field, world):
        self.field = field
        self.maxDrones = 1
        fieldsCount = len(world.fields)
        dronesLeft = len(world.drones) - fieldsCount

        if dronesLeft > 0:
            index = world.sortedFields.index(self.field)
            # we check how many drones an ensemble can use
            # in case of zero it means each ensemble can have one more drone
            # for other cases,
            # in case of 1, for instance, only top ensemble can have one extra drone

            fare = dronesLeft % fieldsCount
            if index >= fare:
                extraDrones = math.floor(dronesLeft / fieldsCount)
            else:
                extraDrones = math.ceil(dronesLeft / fieldsCount)
            self.maxDrones = 1 + extraDrones

    drones: List[Drone] = someOf(Drone)

    @drones.cardinality
    def drones(self):
        return self.maxDrones

    # choose this if not selected
    @drones.select
    def drones(self, drone, otherEnsembles):
        return (drone.state == DroneState.IDLE) and (not any(
            ens for ens in otherEnsembles if isinstance(ens, FieldProtection) and drone in ens.drones)) and drone not in self.drones

    @drones.priority
    def drones(self, drone):
        return - self.field.closestDistanceToDrone(drone)

    def actuate(self):
        for (drone, place) in zip(self.drones, self.field.randomPlaces(len(self.drones))):
            drone.targetFieldPosition = place



class DroneCharger(Ensemble):
    charger: Charger

    def __init__(self, charger):
        self.charger = charger


    drone: Drone = oneOf(Drone)

    @drone.select
    def drone(self, drone, otherEnsembles):
        return not any(ens for ens in otherEnsembles if isinstance(ens, DroneCharger) and drone == ens.drone)


    @drone.priority
    def drone(self, drone):
        return -drone.batteryAfterGetToCharger(self.charger)

    def actuate(self):
        if self.drone.state == DroneState.TERMINATED:
            return False
        self.drone.targetCharger = self.charger
        if self.drone.state == DroneState.CHARGING:
            if self.charger.charge(self.drone):
                # still charging
                return True
            else:
                self.drone.targetCharger = None
                return False
        return True

    def __str__(self):
        return f"{self.drone.id} - {self.charger.id}"
        
    

# class MasterCharger(Ensemble):

#     def __init__(self, world, droneWaitingTimeEstimator: TimeEstimator):
#         self.drones = world.drones
#         self.chargers = world.chargers
#         self.chargerEnsembles = []
#         self.world = world
#         self.droneWaitingTimeEstimator = droneWaitingTimeEstimator

#     def needsCharging(self, drone, closestChargerLocation):
#         # TODO: we need to use the estimator in this function
#         # to find if the drone needs to be charged 
#         return drone.isBatteryCritical(closestChargerLocation)

#     def distanceToClosestCharger(self, drone):
#         distances = [charger.location.distance(drone.location) for charger in self.world.chargers]
#         return min(distances)

#     def actuate(self):
#         potentialEnsembles = []
#         notMarkedDrones = [drone for drone in self.drones if drone not in [ens.drone for ens in self.chargerEnsembles]]

#         for drone in notMarkedDrones:
#             if drone.state != DroneState.TERMINATED:
#                 closestChargerDistance = self.distanceToClosestCharger(drone)
#                 if self.needsCharging(drone, closestChargerDistance):

#                     # first time the ensemble is potential (a drone needs charging) --> collect data
#                     self.droneWaitingTimeEstimator.collectRecordStart(drone.id, {
#                         'drone_battery': drone.battery,
#                         'drone_location_x': drone.location.x,
#                         'drone_location_y': drone.location.y,
#                         'drone_state': int(drone.state),
#                         'closest_charger_distance': closestChargerDistance,
#                     }, self.world.currentTimeStep)

#                     chargingEnsemble = Charging(drone)
#                     potentialEnsembles.append(chargingEnsemble)

#         potentialEnsembles = sorted(potentialEnsembles)

#         for ens in potentialEnsembles:
#             if ens.materialize(self.chargers, self.chargerEnsembles):
#                 ens.drone.targetCharger = ens.charger
#                 self.chargerEnsembles.append(ens)

#                 # first time the ensemble is materialized --> collect data
#                 self.droneWaitingTimeEstimator.collectRecordEnd(ens.drone.id, self.world.currentTimeStep)

#         for ens in self.chargerEnsembles:
#             if not ens.actuate():
#                 self.chargerEnsembles.remove(ens)


# class Charging(Ensemble):
#     drone: Drone

#     def __init__(self, drone):
#         self.drone = drone

#     def priority(self):
#         return -self.drone.battery + (1 if self.drone.state==DroneState.TERMINATED else 0)

#     charger: Charger = oneOf(Charger)

#     @charger.select
#     def charger(self, charger, otherEnsembles):
#         return not any(ens for ens in otherEnsembles if isinstance(ens, Charging) and charger == ens.charger)

#     def distanceToCharger(self, charger):
#         # later check on the field task location
#         # print (f"{charger.id}- {self.drone.targetFieldPosition.distance(charger.location)}")
#         return self.drone.targetFieldPosition.distance(charger.location)

#     @charger.priority
#     def charger(self, charger):
#         return -self.distanceToCharger(charger)

#     def actuate(self):
#         if self.drone.state == DroneState.TERMINATED:
#             return False
#         if self.drone.state == DroneState.CHARGING:
#             if self.charger.charge(self.drone):
#                 # still charging
#                 return True
#             else:
#                 self.drone.targetCharger = None
#                 return False
#         return True

#     def __str__(self):
#         return f"{self.drone.id} - {self.charger.id}"

# class MasterCharger (Ensemble):

#     def __init__ (self,world,droneWaitingTimeEstimator: TimeEstimator):
#         self.world= world
#         self.drones = world.drones
#         self.chargers = world.chargers
#         self.droneWaitingTimeEstimator = droneWaitingTimeEstimator
#         self.runningEnsembles = []
#         self.waitingDrones = set()
    

#     def distanceToClosestCharger(self, drone):
#         distances = [charger.location.distance(drone.location) for charger in self.chargers]
#         return min(distances)

#     def materialize(self):
#         # creates a matrix of drones X chargers
#         self.activeChargerEnsembles = []
#         for drone in self.drones:
#             for charger in self.chargers:
#                 newChargingEnsemble = Charging(drone)
#                 newChargingEnsemble.materialize([charger],[])
#                 self.activeChargerEnsembles.append(newChargingEnsemble)


#     def actuate(self):
#         self.findNewEnsembles()
#         for ens in self.runningEnsembles:
#             if not ens.actuate():
#                 # done charging
#                 self.runningEnsembles.remove(ens)
#                 self.waitingDrones.remove(ens.drone)

#     def findNewEnsembles(self):

#         for drone in self.drones:
#             if drone not in self.waitingDrones:
#                 closestChargerDistance = self.distanceToClosestCharger(drone)
#                 self.droneWaitingTimeEstimator.collectRecordStart(drone.id, {
#                     'drone_battery': drone.battery,
#                     'drone_location_x': drone.location.x,
#                     'drone_location_y': drone.location.y,
#                     'drone_state': int(drone.state),
#                     'closest_charger_distance': closestChargerDistance,
#                 }, self.world.currentTimeStep)

#                 self.waitingDrones.add(drone) 

#         while True:
#             # find all unsigned drones to chargers.
#             potentialNewEnsembles = [ens for ens in self.activeChargerEnsembles if not any(ens.drone==running.drone or ens.charger==running.charger for running in self.runningEnsembles)]
#             # sort them against priority
#             potentialNewEnsembles = sorted(potentialNewEnsembles)
#             # if we still have a few not running ensembles, add the top one and re-check
#             if len(potentialNewEnsembles)>0:
#                 potentialNewEnsembles[0].drone.targetCharger = potentialNewEnsembles[0].charger
#                 self.droneWaitingTimeEstimator.collectRecordEnd(potentialNewEnsembles[0].drone.id, self.world.currentTimeStep)
#                 self.runningEnsembles.append(potentialNewEnsembles[0])
#             else:
#                 break
        
    
        
        

    
    # activeChargerEnsembles: List[Charging] = someOf(Charging) 

    # @activeChargerEnsembles.cardinality
    # def activeChargerEnsembles(self):
    #     return len(self.drones) * len(self.chargers)

    # # choose this if not selected
    # @activeChargerEnsembles.select
    # def activeChargerEnsembles(self, activeChargerEnsemble, otherEnsembles):
    #     return not any([activeChargerEnsemble.drone==ens.drone and activeChargerEnsemble.charger == ens.charger for ens in otherEnsembles])

    # @activeChargerEnsembles.priority
    # def activeChargerEnsembles(self, activeChargerEnsemble):
    #     return - activeChargerEnsemble.priority()


  


  