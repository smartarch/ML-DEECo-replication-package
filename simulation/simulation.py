from simulation.components import Bird, Drone, Point, Field, Charger, DroneState
from utils.serialization import Log
from utils.visualizers import Visualizer

CLASSNAMES = {
    'drones': Drone,
    'birds': Bird,
    'chargers': Charger,
    'fields': Field,
}


class World:
    """
        A world class consist of Drones, Birds, Fields and Chargers.
    """

    MAX_RANDOMPOINTS = 100

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
            "waiting_drones_length",
            "accepted_queues_length",
            "charging_drones_length",
        ])

        self.chargerLogs = []
        for charger in self.chargers:
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


WORLD = None


class Simulation:

    def __init__(self, world, folder, visualize):
        self.visualize = visualize
        self.world = world
        self.folder = folder

        global WORLD
        WORLD = world

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

        for charger in self.world.chargers:
            charger.assignWaitingTimeEstimator(estimation.createEstimator())

        from ensembles.field_protection import ensembles as fieldProtectionEnsembles
        from ensembles.drone_charging import ensembles as droneChargingEnsembles
        potentialEnsembles = fieldProtectionEnsembles + droneChargingEnsembles

        if self.visualize:
            visualizer = Visualizer(self.world)
            visualizer.drawFields()

        for i in range(self.world.maxSteps):
            if verbose > 2:
                print(f"        Step {i + 1}:")
            self.world.currentTimeStep = i
            for component in components:
                component.actuate()

                if verbose > 3:
                    print(f"            {component}")

            initializedEnsembles = []

            potentialEnsembles = sorted(potentialEnsembles)

            for ens in potentialEnsembles:
                if ens.materialize(components, initializedEnsembles):
                    initializedEnsembles.append(ens)
                    ens.actuate(verbose)

            for chargerIndex in range(len(self.world.chargers)):
                charger = self.world.chargers[chargerIndex]
                potentialDrones = len(charger.potentialDrones) if len(charger.potentialDrones) > 0 else 1
                self.world.chargerLogs[chargerIndex].register([
                    # sum([drone.battery for drone in charger.potentialDrones])/potentialDrones,
                    len(charger.chargingDrones),
                    len(charger.acceptedDrones),
                    len(charger.waitingDrones),
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
                ens.actuate(0)
