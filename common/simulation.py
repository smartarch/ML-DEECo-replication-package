import random
from common.components import Agent, Bird, Drone, Point, Field, Charger, Component, DroneState, BirdState
from common.tasks import getPotentialEnsembles 
# from common.timetasks import getNewAlertChangingEnsembles
from common.serialization import Log
from common.visualizers import Visualizer

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

    def findDrones(self,droneStates):
        return [drone for drone in self.drones if drone.state in droneStates]
    
    def exceptDrones(self,droneStates):
        return [drone for drone in self.drones if drone.state not in droneStates]


    def findBirds(self,birdStates):
        return [bird for bird in self.birds if bird.state in birdStates]
    
    def exceptBirds(self,birdStates):
        return [bird for bird in self.birds if bird.state not in birdStates]

class Simulation:

    def __init__(self, world, folder, visualize):
        self.visualize = visualize
        self.world = world
        self.folder = folder

    def collectStatistics(self):
        return [
            len([drone for drone in self.world.drones if drone != DroneState.TERMINATED]),
            sum([bird.ate for bird in self.world.birds]),
            sum([charger.energyConsumed for charger in self.world.chargers])
        ]

    def run(self, filename, estimation, verbose):

        components = []

        components.extend(self.world.drones)
        components.extend(self.world.birds)
        components.extend(self.world.chargers)

        for charger in self.world.chargers:
            charger.waitingTimeEstimator = estimation.createEstimator()

        potentialEnsembles = getPotentialEnsembles(self.world)

        # masterCharger = MasterCharger(self.world, droneWaitingTimeEstimator)
        # masterCharger.materialize()

        if self.visualize:
            visualizer = Visualizer(self.world)
            visualizer.drawFields()

        for i in range(self.world.maxSteps):
            if verbose > 2:
                print(f"        iteration {i + 1}:")
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

            if self.visualize:
                visualizer.drawComponents(i + 1)

        if self.visualize:
            visualizer.createAnimation(f"{self.folder}/simulation-{filename}.gif")

        finalLog = self.collectStatistics()

        return estimation, finalLog

    def actuateEnsembles(self,potentialEnsembles,components):
        initializedEnsembles = []
        potentialEnsembles = sorted(potentialEnsembles)
        for ens in potentialEnsembles:
            if ens.materialize(components, initializedEnsembles):
                initializedEnsembles.append(ens)
                ens.actuate(0)

    def timeRun (self,timeModel,timeLog,maxIterations):
        components = []

        components.extend(self.world.drones)
        components.extend(self.world.birds)
        components.extend(self.world.chargers)
        totalPlaces = sum([len(field.places) for field in self.world.fields])
        potentialEnsembles = getPotentialEnsembles(self.world)
 
        timeLog.register([0,0, 0, 0, 0, 0, 0 ])

        # collect some statistics before running
        aliveDrones = len(self.world.exceptDrones([DroneState.TERMINATED]))
        if aliveDrones<=0:
            return timeLog

        for i in range(maxIterations):
            self.world.currentTimeStep = i
            for component in components:
                component.actuate()

            self.actuateEnsembles(potentialEnsembles,components)
            
            timeLog.add([
                0, # max_time_step max time step doesn't change
                0, # dead_drone_rate can be calculated in O(1) timespace
                0, # charge_alert is constant at this rate
                len(self.world.findDrones([DroneState.PROTECTING,DroneState.MOVING_TO_FIELD]))/(maxIterations*aliveDrones), # average_protecting_time
                len(self.world.findDrones([DroneState.MOVING_TO_CHARGER]))/(maxIterations*aliveDrones), # average_protecting_time
                len(self.world.findDrones([DroneState.CHARGING]))*self.world.chargingRate,
                len(self.world.findBirds([BirdState.EATING])),

            ])

        timeLog.add([
            maxIterations,
            (aliveDrones - len(self.world.exceptDrones([DroneState.TERMINATED])))/aliveDrones,
            self.world.drones[0].alert,
            0,0,0,0
        ])
        return timeLog