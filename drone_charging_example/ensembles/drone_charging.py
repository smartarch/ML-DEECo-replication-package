import math
from typing import List, TYPE_CHECKING

from world import ENVIRONMENT, WORLD
from components.drone_state import DroneState
from components.drone import Drone

from ml_deeco.estimators import NumericFeature, CategoricalFeature
from ml_deeco.simulation import Ensemble, someOf
from ml_deeco.utils import verbosePrint

if TYPE_CHECKING:
    from components.charger import Charger

# The order of the ensembles is:
#  1. DroneChargingPreassignment
#  2. DroneChargingAssignment
#  3. AcceptedDronesAssignment

class DroneChargingPreAssignment(Ensemble):
    """

    The Pre-assignment tells the drones that where is the potential charger and vise-versa.
    It has to come first; therefore, it has priority of 3.

    Parameters
    ----------
    charger : Charger
        The charger component.

    Properties:
    ---------
    drones: List (someOf) Drones
    """
    charger: 'Charger'

    def __init__(self, charger: 'Charger'):
        """

        Initiate the pre-assignment charger ensemble.

        Parameters
        ----------
        charger : Charger
            the targer charger.
        """
        self.charger = charger

    def priority(self):
        """

        Arbitrary as 3, to make sure the ensemble works before others.

        Returns
        -------
        int
            3
        """
        return 3

    drones: List[Drone] = someOf(Drone)

    @drones.cardinality
    def drones(self):
        """

        The length of drones list is defined.

        Returns
        -------
        tuple
            [0, all drones in the environment]
        """
        return 0, ENVIRONMENT.droneCount

    @drones.select
    def drones(self, drone, otherEnsembles):
        """

        Defines which drones are the potential ones to the charger. 

        Parameters
        ----------
        drone : Drone
            The query drone.
        otherEnsembles : list
            unused in this concept, followed the definition of ensemble.

        Returns
        -------
        bool
            If the drone is selected.
        """
        return drone.state not in (DroneState.TERMINATED, DroneState.MOVING_TO_CHARGER, DroneState.CHARGING) and \
            drone.findClosestCharger() == self.charger

    def actuate(self):
        """

        For all selected drones, the potential charger is set.
        For the charger, the list of potential drones is set.
        """
        self.charger.potentialDrones = self.drones
        for drone in self.drones:
            drone.closestCharger = self.charger
        verbosePrint(f"DroneChargingPreassignment: assigned {len(self.drones)} to {self.charger.id}", 4)

class DroneChargingAssignment(Ensemble):
    """

    The drone charging assignment checks if any potential drones requires charging.
    In this ensemble, the data for ML-Based model is collected.
    The priority of this ensemble is 2, ensuring that it will run before accepting.
    The drones that are selected will be added to the waiting queue.

    Parameters
    ----------
    charger : Charger
        The charger component.

    Properties:
    ---------
    drones: List (someOf) Drones With Time Estimator
    """
    charger: 'Charger'

    def __init__(self, charger: 'Charger'):
        """
        
        initiate the charging ensemble.

        Parameters
        ----------
        charger : Charger
            The targetted charger.
        """
        self.charger = charger

    def priority(self):
        """

        Arbitrary set as 2, ensuring it will come after Pre-Assignment ensemble and before the accepting ensemble.

        Returns
        -------
        int
            2
        """
        return 2

    drones: List[Drone] = someOf(Drone).withTimeEstimate().using(WORLD.waitingTimeEstimator)

    @drones.cardinality
    def drones(self):
        """

        The length of drones.

        Returns
        -------
        tuple
            [0, all drones in the environment]
        """
        return 0, ENVIRONMENT.droneCount

    @drones.select
    def drones(self, drone, otherEnsembles):
        """

        Select the drone to be in the waiting queue, which:
        1-  Not Terminated 
        2-  Drone in potentail drones.
        3-  Needs charging: in ML-based, the waiting time is estimated


        Parameters
        ----------
        drone : Drone
            The query drone.
        otherEnsembles : list
            unused here, following the definition of the ensemble.

        Returns
        -------
        bool
            if True, the drone is selected to be in waiting queue.
        """
        if drone.state == DroneState.TERMINATED:
            return False
        waitingTimeEstimate = self.drones.estimate(drone)
        timeToFlyToCharger = drone.timeToFlyToCharger()
        # needs charging
        return drone in self.charger.potentialDrones and \
            drone.needsCharging(waitingTimeEstimate + timeToFlyToCharger)

    # region Features

    @drones.estimate.input(NumericFeature(0, 1))
    def battery(self, drone):
        return drone.battery

    @drones.estimate.input(CategoricalFeature(DroneState))
    def drone_state(self, drone):
        return drone.state

    @drones.estimate.input(NumericFeature(0, math.sqrt(ENVIRONMENT.mapWidth ** 2 + ENVIRONMENT.mapHeight ** 2)))
    def charger_distance(self, drone):
        return self.charger.location.distance(drone.location)

    @drones.estimate.input(NumericFeature(0, ENVIRONMENT.chargerCapacity))
    def accepted_drones_count(self, drone):
        return len(self.charger.acceptedDrones)

    @drones.estimate.input(NumericFeature(0, ENVIRONMENT.chargerCapacity * ENVIRONMENT.chargerCount))
    def charger_capacity(self, drone):
        return ENVIRONMENT.chargerCapacity

    @drones.estimate.input(NumericFeature(0, 1))
    def neighbor_drones_average_battery(self, drone):
        if drone.targetField is not None:
            k = len(drone.targetField.protectingDrones)
            if k == 0:
                return 0
            return sum([drone.battery for drone in drone.targetField.protectingDrones])/k
        else:
            return 0

    @drones.estimate.input(NumericFeature(0, 1))
    def neighbor_drones(self, drone):
        if drone.targetField is not None:
            return len(drone.targetField.protectingDrones)/len(drone.targetField.places)
        else:
            return 0

    @drones.estimate.input(NumericFeature(0, 1))
    def potential_drones(self, drone):
        return len(self.charger.potentialDrones)

    @drones.estimate.input(NumericFeature(0, ENVIRONMENT.chargerCapacity))
    def accepted_drones_missing_battery(self, drone):
        return sum([1 - drone.battery for drone in self.charger.acceptedDrones])

    @drones.estimate.input(NumericFeature(0, ENVIRONMENT.chargerCapacity))
    def charging_drones_count(self, drone):
        return len(self.charger.chargingDrones)

    @drones.estimate.input(NumericFeature(0, ENVIRONMENT.chargerCapacity))
    def charging_drones_missing_battery(self, drone):
        return sum([1 - drone.battery for drone in self.charger.chargingDrones])

    @drones.estimate.input(NumericFeature(0, ENVIRONMENT.droneCount))
    def potential_drones_with_lower_battery(self, drone):
        return len([d for d in self.charger.potentialDrones if d.battery < drone.battery])

    @drones.estimate.input(NumericFeature(0, ENVIRONMENT.chargerCapacity))
    def waiting_drones_count(self, drone):
        return len(self.charger.waitingDrones)

    @drones.estimate.input(NumericFeature(0, ENVIRONMENT.droneCount))
    def waiting_drones_with_lower_battery(self, drone):
        return len([d for d in self.charger.waitingDrones if d.battery < drone.battery])

    # endregion

    @drones.estimate.inputsValid
    @drones.estimate.conditionsValid
    def is_preassigned(self, drone):

        # return drone in self.drones
        return drone in self.charger.potentialDrones

    @drones.estimate.condition
    def is_accepted(self, drone):
        """

        The Target value for estimation. 
        The time estimator, calculates the time drone is in waiting queue,
        and then it calculates when the drone is accepted.
        The difference is the waited time.

        Parameters
        ----------
        drone : Drone
            The candiadate drone.

        Returns
        -------
        bool
            If True, the drone is accepted
        """
        return drone in self.charger.acceptedDrones

    def actuate(self):
        """

        The waiting queue will be updated to the list of current drones.
        """
        verbosePrint(f"DroneChargingAssignment: assigned {len(self.drones)} to {self.charger.id}", 4)
        self.charger.waitingDrones = self.drones


class AcceptedDronesAssignment(Ensemble):
    """

    This ensemble only ensure that the drones are being charged in with the charger.

    Parameters
    ----------
    charger : Charger
        The charger component.

    Properties:
    ---------
    drones: List (someOf) Drones 
    """
    charger: 'Charger'

    def __init__(self, charger: 'Charger'):
        """

        Initiate the ensemble.

        Parameters
        ----------
        charger : Charger
            The targeted charger.
        """
        self.charger = charger

    def priority(self):
        """

        Arbitrary set as 1, ensuring it will come after Pre-Assignment ensemble and the accepting ensemble.

        Returns
        -------
        int
            1
        """
        return 1  # The order of AcceptedDronesAssignment ensembles can be arbitrary as they don't influence each other.

    drones: List[Drone] = someOf(Drone)

    @drones.cardinality
    def drones(self):
        """

        The length of drones.

        Returns
        -------
        tuple
            [0, charger capacity]
        """
        return 0, self.charger.acceptedCapacity

    @drones.select
    def drones(self, drone, otherEnsembles):
        """

        Selects the drone to be charrged :
        1- the drone is not terminated
        2- drone is accepted by the charger or the drone is in waiting queue
        3- the charger will be free before/close to the time drone flies there

        Parameters
        ----------
        drone : Drone
            The query drone.
        otherEnsembles : list
            unused in this concept, following the definition of ensemble.

        Returns
        -------
        bool
            If True, the drone is accepted.
        """
        if drone.state == DroneState.TERMINATED:
            return False
        # was accepted before or needs charging (is waiting) and the charger will be free
        return drone in self.charger.acceptedDrones or \
            drone in self.charger.waitingDrones and \
            self.charger.timeToDoneCharging(len(self.drones)) <= drone.timeToFlyToCharger()

    @drones.utility
    def drones(self, drone):
        """

        sorts the drone toward their time to done charging.

        Parameters
        ----------
        drone : Drone
            The candidate drone.

        Returns
        -------
        int
            time to done charing.
        """
        if drone in self.charger.acceptedDrones:
            return 1  # keep the accepted drones from previous time steps
        return -drone.timeToDoneCharging()

    def actuate(self):
        """

        Updates the accepted drone list.
        """
        verbosePrint(f"AcceptedDronesAssignment: assigned {len(self.drones)} to {self.charger.id}", 4)
        self.charger.acceptedDrones = self.drones
        for drone in self.drones:
            drone.targetCharger = self.charger


ensembles: List[Ensemble]


def getEnsembles():
    """

    creates a list of ensembles for all types of charging assignments.

    Returns
    -------
    list
        List of ensembles.
    """
    global ensembles

    ensembles = \
        [DroneChargingPreAssignment(charger) for charger in WORLD.chargers] + \
        [DroneChargingAssignment(charger) for charger in WORLD.chargers] + \
        [AcceptedDronesAssignment(charger) for charger in WORLD.chargers]

    return ensembles
