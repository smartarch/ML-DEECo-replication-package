from typing import List, TYPE_CHECKING

from utils.serialization import Log

if TYPE_CHECKING:
    from estimators.estimation import Estimation


MAX_RANDOM_POINTS = 100


class Environment:
    """
    Constants regarding the simulation environment.
    """

    maxSteps = 500
    mapWidth = 100
    mapHeight = 100

    droneRadius = 5
    birdSpeed = 1
    droneSpeed = 1

    droneBatteryRandomize = 0
    droneMovingEnergyConsumption = 0.01
    droneProtectingEnergyConsumption = 0.005
    chargingRate = 0.04
    chargerCapacity = 1

    droneCount = 8
    birdCount = 20
    chargerCount = 2
    chargerPositions = []
    fieldCount = 2
    fieldPositions = []

    def __init__(self):
        if 'ENVIRONMENT' in locals():
            raise RuntimeError("Do not create a new instance of the Environment. Use the ENVIRONMENT global variable instead.")

    def loadConfig(self, config: dict):
        for conf, confValue in config.items():
            if conf in Environment.__dict__:
                self.__dict__[conf] = confValue
        self.droneCount = config['drones']
        self.birdCount = config['birds']
        self.chargerCount = len(config['chargers'])
        self.chargerPositions = config['chargers']
        self.fieldCount = len(config['fields'])
        self.fieldPositions = config['fields']


ENVIRONMENT = Environment()


class World:
    """
    The simulated world.
    """
    waitingTimeEstimation: 'Estimation'
    droneBatteryEstimation: 'Estimation'

    def __init__(self):
        if 'WORLD' in locals():
            raise RuntimeError("Do not create a new instance of the World. Use the WORLD global variable instead.")
        self.estimations = []

    # noinspection PyAttributeOutsideInit
    def reset(self):
        """
        Call this before the world is used.
        """
        from simulation.components import Bird, Field, Point
        from simulation.drone import Drone
        from simulation.charger import Charger

        self.currentTimeStep = 0

        self.drones: List[Drone] = [Drone(Point.randomPoint()) for _ in range(ENVIRONMENT.droneCount)]
        self.birds: List[Bird] = [Bird(Point.randomPoint()) for _ in range(ENVIRONMENT.birdCount)]
        self.chargers: List[Charger] = [Charger(point) for point in ENVIRONMENT.chargerPositions]
        self.fields: List[Field] = [Field(points) for points in ENVIRONMENT.fieldPositions]

        self.totalPlaces = sum([len(f.places) for f in self.fields])
        self.sortedFields = sorted(self.fields, key=lambda field: -len(field.places))

        self.emptyPoints = []
        for i in range(MAX_RANDOM_POINTS):
            p = Point.random(0, 0, ENVIRONMENT.mapWidth, ENVIRONMENT.mapHeight)
            if self.isPointField(p):
                i = i - 1
            else:
                self.emptyPoints.append(p)

        self.createLogs()

    def initEstimations(self):
        """Initialize the estimations. This has to be called after the components and ensembles are imported."""
        for est in self.estimations:
            est.init()

    # noinspection PyAttributeOutsideInit
    def createLogs(self):

        self.chargerLog = Log([
            "current_time_step",
            "drone_id",
            "battery",
            "estimated_waiting",
            "energy_to_fly_to_charger",
            "time_to_done_charging",
            "charger",
            "potential_drones_length",
            "waiting_drones_length",
            "accepted_queues_length",
            "charging_drones_length",
        ])

        self.chargerLogs = []
        for _ in self.chargers:
            self.chargerLogs.append(Log([
                "Charging Drones",
                "Accepted Drones",
                "Waiting Drones",
                "Potential Drones",
            ]))

    def isProtectedByDrone(self, point):
        for drone in self.drones:
            if drone.isProtecting(point):
                return True
        return False

    def isPointField(self, point):
        for field in self.fields:
            if field.isPointOnField(point):
                return True
        return False

    def findDrones(self, droneStates):
        return [drone for drone in self.drones if drone.state in droneStates]

    def exceptDrones(self, droneStates):
        return [drone for drone in self.drones if drone.state not in droneStates]

    def findBirds(self, birdStates):
        return [bird for bird in self.birds if bird.state in birdStates]

    def exceptBirds(self, birdStates):
        return [bird for bird in self.birds if bird.state not in birdStates]


WORLD = World()
