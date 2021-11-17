
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
        if self.drone not in self.charger.droneQueue:
            self.charger.droneQueue.append(self.drone)
            self.drone.targetCharger = self.charger