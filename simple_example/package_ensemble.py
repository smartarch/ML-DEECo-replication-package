from drone import Drone, DroneState
from ml_deeco.simulation import Ensemble, oneOf


class PackageEnsemble(Ensemble):

    def __init__(self, location):
        self.location = location

    drone = oneOf(Drone)

    @drone.select
    def is_available(self, drone, otherEnsembles):
        return drone.state == DroneState.AVAILABLE

    def actuate(self):
        self.drone.target = self.location
