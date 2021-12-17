from simulation.components import Drone, Charger, DroneState
from simulation.ensemble import Ensemble, someOf
from simulation.simulation import WORLD
from typing import List


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
        if drone.state == DroneState.TERMINATED:
            return False

        # was accepted before or needs charging
        cond = drone in self.charger.acceptedDrones or \
            drone in self.charger.potentialDrones and \
            drone.needsCharging()

        cond = cond and self.charger.timeToDoneCharging() <= drone.timeToFlyToCharger()

        if cond:
            # TODO(MT): move the estimator to the ensemble
            self.charger.waitingTimeEstimator.collectRecordStart(drone.id, self.charger, drone, WORLD.currentTimeStep)
        return cond

    @drones.priority
    def drones(self, drone):
        if drone in self.charger.acceptedDrones:
            return 1  # keep the accepted drones from previous time steps  # TODO: think about this later
        return -drone.timeToDoneCharging()

    def actuate(self, verbose):

        # only for printing
        if verbose > 3:
            print(f"            Charging Ensemble: assigned {len(self.drones)} to {self.charger.id}")

        for drone in self.drones:
            # TODO(MT): move the estimator to the ensemble
            self.charger.waitingTimeEstimator.collectRecordEnd(drone.id, WORLD.currentTimeStep)
            self.charger.world.chargerLog.register([
                drone.world.currentTimeStep,
                drone.id,
                drone.battery,
                drone.computeFutureBattery(),
                drone.estimateWaitingEnergy(drone.closestCharger),
                drone.energyToFlyToCharger(),
                drone.timeToDoneCharging(),
                self.charger.id,
                len(self.charger.potentialDrones),
                len(self.charger.acceptedDrones),
                len(self.charger.chargingDrones),
            ])

        self.charger.acceptedDrones = self.drones


ensembles = \
    [PotentialDronesAssignment(charger) for charger in WORLD.chargers] +\
    [AcceptedDronesAssignment(charger) for charger in WORLD.chargers]
