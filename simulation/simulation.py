from typing import Type, Optional

from simulation.components import Bird, Point, Field
from simulation.charger import getChargerClass
from simulation.drone import DroneState, getDroneClass
from utils.serialization import Log
from utils.verbose import verbosePrint
from utils.visualizers import Visualizer


class World:
    """
        A world class consist of Drones, Birds, Fields and Chargers.
    """

    MAX_RANDOMPOINTS = 100
    Drone: Optional[Type] = None
    Charger: Optional[Type] = None

    def __init__(self, confDict):
        """
            initiate a world with a YAML configuration file
            component:X a number or list of points for given component

        """
        self.maxSteps = 500
        self.mapWidth = 100
        self.mapHeight = 100
        self.droneRadius = 5
        self.birdSpeed = 1
        self.droneSpeed = 1
        self.droneBatteryRandomize = 0
        self.droneMovingEnergyConsumption = 0.01
        self.droneProtectingEnergyConsumption = 0.005
        self.chargingRate = 0.2
        self.chargerCapacity = 1

        self.currentTimeStep = 0

        self.Drone = getDroneClass(self)
        Drone = self.Drone
        self.Charger = getChargerClass(self)
        Charger = self.Charger

        CLASSNAMES = {
            'drones': Drone,
            'birds': Bird,
            'chargers': Charger,
            'fields': Field,
        }

        for conf, confValue in confDict.items():
            if conf not in CLASSNAMES:
                self.__dict__[conf] = confValue

        Point.MaxWidth = self.mapWidth
        Point.MaxHeight = self.mapHeight

        for conf, confValue in confDict.items():
            if conf in CLASSNAMES:
                if isinstance(confValue, int):
                    confDict[conf] = []
                    for i in range(confValue):
                        confDict[conf].append(Point.randomPoint())

        self.drones = []
        self.birds = []
        self.chargers = []
        self.fields = []

        for point in confDict['drones']:
            self.drones.append(Drone(point, self))

        for point in confDict['birds']:
            self.birds.append(Bird(point, self))

        for point in confDict['chargers']:
            self.chargers.append(Charger(point, self))

        for fieldPoints in confDict['fields']:
            self.fields.append(Field(fieldPoints, self))

        self.totalPlaces = sum([len(f.places) for f in self.fields])
        self.sortedFields = sorted(self.fields, key=lambda field: -len(field.places))

        self.emptyPoints = []
        for i in range(World.MAX_RANDOMPOINTS):
            p = Point.random(0, 0, self.mapWidth, self.mapHeight)
            if self.isPointField(p):
                i = i - 1
            else:
                self.emptyPoints.append(p)

        self.chargerLog = Log([
            "current_time_step",
            "drone_id",
            "battery",
            "future_battery",
            "estimated_waiting",
            "energy_needed_to_charge",
            "time_to_charge",
            "charger",
            "potential_drones_length",
            "accepted_queues_length",
            "charging_drones_length",
        ])

        self.chargerLogs = []
        for charger in self.chargers:
            self.chargerLogs.append(Log([
                "Charging Drones",
                "Accepted Drones",
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


class Simulation:

    def __init__(self, world, folder, visualize):
        self.visualize = visualize
        self.world = world
        self.folder = folder

    def collectStatistics(self):
        return [
            len([drone for drone in self.world.drones if drone.state != DroneState.TERMINATED]),
            sum([bird.ate for bird in self.world.birds]),
            sum([charger.energyConsumed for charger in self.world.chargers])
        ]

    def run(self, filename, estimation, verbose, args):

        components = []

        components.extend(self.world.drones)
        components.extend(self.world.birds)
        components.extend(self.world.chargers)

        from ensembles.field_protection import getEnsembles as fieldProtectionEnsembles
        from ensembles.drone_charging import getEnsembles as droneChargingEnsembles
        potentialEnsembles = fieldProtectionEnsembles(self.world) + droneChargingEnsembles(self.world)

        if self.visualize:
            visualizer = Visualizer(self.world)
            visualizer.drawFields()

        for i in range(self.world.maxSteps):
            verbosePrint(f"Step {i + 1}:", 3)
            self.world.currentTimeStep = i
            for component in components:
                component.actuate()
                verbosePrint(f"{component}", 4)

            initializedEnsembles = []

            potentialEnsembles = sorted(potentialEnsembles)

            for ens in potentialEnsembles:
                if ens.materialize(components, initializedEnsembles):
                    initializedEnsembles.append(ens)
                    ens.actuate()

            for chargerIndex in range(len(self.world.chargers)):
                charger = self.world.chargers[chargerIndex]
                potentialDrones = len(charger.potentialDrones) if len(charger.potentialDrones) > 0 else 1
                self.world.chargerLogs[chargerIndex].register([
                    # sum([drone.battery for drone in charger.potentialDrones])/potentialDrones,
                    len(charger.chargingDrones),
                    len(charger.acceptedDrones),
                    potentialDrones,
                ])

            if self.visualize:
                visualizer.drawComponents(i + 1)

        if self.visualize:
            visualizer.createAnimation(f"{self.folder}/animations/{filename}.gif")

        self.world.chargerLog.export(f"{self.folder}/charger_logs/{filename}.csv")
        totalLog = self.collectStatistics()

        return estimation, totalLog, self.world.chargerLogs

    def actuateEnsembles(self, potentialEnsembles, components):
        initializedEnsembles = []
        potentialEnsembles = sorted(potentialEnsembles)
        for ens in potentialEnsembles:
            if ens.materialize(components, initializedEnsembles):
                initializedEnsembles.append(ens)
                ens.actuate()
