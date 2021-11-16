
from source.ensembles.ensemble import Ensemble, oneOf
from source.components.charger import Charger
from source.components.drone import Drone


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
        if self.charger.client == None:
            if self.needsCharging():
                self.charger.client =self.drone
                
        self.drone.targetCharger = self.charger




# class PrivateChargerAssignment(Ensemble):
#     charger: Charger

#     def __init__(self, charger):
#         self.charger = charger

#     def needsCharging(self, drone):
#         return drone.criticalBattery()

#     # check the distance to the charger
#     def distanceToDrone(self, drone):
#         return self.charger.location.distance(drone.location)

#     drone: Drone = oneOf(Drone)

#     @drone.select
#     def drone(self, drone, otherEnsembles):
#         return not any(ens for ens in otherEnsembles if isinstance(ens, PrivateChargerAssignment) and ens.drone == drone) and self.needsCharging(drone)

#     @drone.priority
#     def drone(self, drone):
#         return -self.distanceToDrone(drone) * (drone.battery+0.01)

#     def actuate(self):
#         if self.charger.client == None:
#             self.charger.client =self.drone
#             return False
#         self.drone.targetCharger = self.charger
#         return True

