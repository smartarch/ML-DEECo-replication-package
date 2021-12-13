from common.components import Drone, Field, Charger, DroneState
from common.ensemble import Ensemble, someOf, oneOf
from typing import List

class ChangeChargeAlert(Ensemble):
    
    def __init__(self,newAlert):
        self.newAlert = newAlert

    drone: Drone = oneOf(Drone)

    def priority(self):
        return 1


    @drone.select
    def drone(self, drone, otherEnsembles):
        conditions = [
            not any(ens for ens in otherEnsembles if isinstance(ens, ChangeChargeAlert) and drone == ens.drone),
            drone.state != DroneState.TERMINATED,  
            drone.alert != self.newAlert
        ]
        return all(conditions)

    @drone.priority
    def drone(self, drone):
        return - drone.battery

    def actuate(self, verbose):

        if verbose > 3:
            print(f"            Alert Tunning Ensemble: alerting {self.drone.id} at battery below {self.newAlert}")

        self.drone.alert = self.newAlert

def getNewAlertChangingEnsembles(count, newAlert):
    alertChangingEnsembles = []
    for i in range(count):
        alertChangingEnsembles.append(ChangeChargeAlert(newAlert))

    return alertChangingEnsembles