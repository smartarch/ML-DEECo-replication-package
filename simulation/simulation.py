from simulation.drone_state import DroneState
from simulation.world import WORLD, ENVIRONMENT
from utils.verbose import verbosePrint
from utils.visualizers import Visualizer
from utils.serialization import Log


# TODO: as the world is global, this might be only a function (or multiple functions) instead of a class
class Simulation:

    def __init__(self, world, folder, visualize):
        self.visualize = visualize
        self.world = world
        self.folder = folder
        self.MAXDRONES = ENVIRONMENT.droneCount
        self.MAXDAMAGE = ENVIRONMENT.birdCount * ENVIRONMENT.maxSteps
        self.MAXENERGY = ENVIRONMENT.chargerCount * ENVIRONMENT.chargerCapacity * ENVIRONMENT.chargingRate * ENVIRONMENT.maxSteps



    def collectStatistics(self):
        return [

            len([drone for drone in self.world.drones if drone.state != DroneState.TERMINATED]),
            sum([bird.ate for bird in self.world.birds]),
            sum([charger.energyConsumed for charger in self.world.chargers])
        ]

    def collectRates(self, previousRates):
        if previousRates is None:
            previousRates ={
                'Damage':0,
                'Energy':0,

            }
        return [
            WORLD.currentTimeStep, 
            WORLD.drones[0].alert,
            ENVIRONMENT.droneBatteryRandomize,
            len([drone for drone in self.world.drones if drone.state != DroneState.TERMINATED]),
            len([drone for drone in self.world.drones if drone.state != DroneState.TERMINATED])/self.MAXDRONES,
            sum([bird.ate for bird in self.world.birds])-previousRates['Damage'],
            sum([bird.ate for bird in self.world.birds]),
            sum([charger.energyConsumed for charger in self.world.chargers])-previousRates['Energy'],
            sum([charger.energyConsumed for charger in self.world.chargers])
        ]
    def run(self, filename, args):

        components = []

        components.extend(self.world.drones)
        components.extend(self.world.birds)
        components.extend(self.world.chargers)

        from ensembles.field_protection import getEnsembles as fieldProtectionEnsembles
        from ensembles.drone_charging import getEnsembles as droneChargingEnsembles
        potentialEnsembles = fieldProtectionEnsembles(self.world) + droneChargingEnsembles(self.world)

        WORLD.initEstimators()

        if self.visualize:
            visualizer = Visualizer(self.world)
            visualizer.drawFields()

        for i in range(ENVIRONMENT.maxSteps):
            verbosePrint(f"Step {i + 1}:", 3)
            self.world.currentTimeStep = i

            # Ensembles
            initializedEnsembles = []

            potentialEnsembles = sorted(potentialEnsembles)

            for ens in potentialEnsembles:
                if ens.materialize(components, initializedEnsembles):
                    initializedEnsembles.append(ens)
                    ens.actuate()
            for ens in initializedEnsembles:
                ens.collectEstimatesData()

            # Components
            for component in components:
                component.actuate()
                verbosePrint(f"{component}", 4)
            for component in components:
                component.collectEstimatesData()

            # Collect statistics
            for chargerIndex in range(len(self.world.chargers)):
                charger = self.world.chargers[chargerIndex]
                accepted = set(charger.acceptedDrones)
                waiting = set(charger.waitingDrones)
                potential = set(charger.potentialDrones)
                self.world.chargerLogs[chargerIndex].register([
                    # sum([drone.battery for drone in charger.potentialDrones])/potentialDrones,
                    len(charger.chargingDrones),
                    len(accepted),
                    len(waiting - accepted),
                    len(potential - waiting - accepted),
                ])

            if self.visualize:
                visualizer.drawComponents(i + 1)

        if self.visualize:
            verbosePrint(f"Saving animation...", 3)
            visualizer.createAnimation(f"{self.folder}/animations/{filename}.gif")
            verbosePrint(f"Animation saved.", 3)

        self.world.chargerLog.export(f"{self.folder}/charger_logs/{filename}.csv")
        totalLog = self.collectStatistics()

        return totalLog, self.world.chargerLogs


    def quickrun(self, filename, args):
        log = Log([
            'Iterations',
            'Charge Alert',
            'Battery Randomize',
            'Alive Drones',
            'Drone Live Rate',
            'Damage',
            'Cumulative Damage',
            'Consumed Energy',
            'Cumulative Consumed Energy'
            ])
        components = []

        components.extend(self.world.drones)

        components.extend(self.world.birds)
        components.extend(self.world.chargers)

        from ensembles.field_protection import getEnsembles as fieldProtectionEnsembles
        from ensembles.drone_charging import getEnsembles as droneChargingEnsembles
        potentialEnsembles = fieldProtectionEnsembles(self.world) + droneChargingEnsembles(self.world)

        WORLD.initEstimators()

        if self.visualize:
            visualizer = Visualizer(self.world)
            visualizer.drawFields()
        previousRates = None
        for i in range(ENVIRONMENT.maxSteps):
            verbosePrint(f"Step {i + 1}:", 3)
            self.world.currentTimeStep = i

            # Ensembles
            initializedEnsembles = []

            potentialEnsembles = sorted(potentialEnsembles)

            for ens in potentialEnsembles:
                if ens.materialize(components, initializedEnsembles):
                    initializedEnsembles.append(ens)
                    ens.actuate()

            # Components
            for component in components:
                component.actuate()
                component.collectEstimatesData()
                verbosePrint(f"{component}", 4)

            
            if i % 50 == 0:
                rate = self.collectRates(previousRates)
                previousRates ={
                    'Damage':rate[5],
                    'Energy':rate[7]
                }
                log.register(rate)

            # # Collect statistics
            # for chargerIndex in range(len(self.world.chargers)):
            #     charger = self.world.chargers[chargerIndex]
            #     accepted = set(charger.acceptedDrones)
            #     waiting = set(charger.waitingDrones)
            #     potential = set(charger.potentialDrones)
            #     self.world.chargerLogs[chargerIndex].register([
            #         # sum([drone.battery for drone in charger.potentialDrones])/potentialDrones,
            #         len(charger.chargingDrones),
            #         len(accepted),
            #         len(waiting - accepted),
            #         len(potential - waiting - accepted),
            #     ])

            if self.visualize:
                visualizer.drawComponents(i + 1)

        if self.visualize:
            verbosePrint(f"Saving animation...", 3)
            visualizer.createAnimation(f"{self.folder}/animations/{filename}.gif")
            verbosePrint(f"Animation saved.", 3)

        self.world.chargerLog.export(f"{self.folder}/charger_logs/{filename}.csv") 
        
        WORLD.currentTimeStep = ENVIRONMENT.maxSteps
        log.register(self.collectRates(previousRates))
        log.export(f"{self.folder}/{filename}.csv")
        return self.collectStatistics(), self.world.chargerLogs

    def actuateEnsembles(self, potentialEnsembles, components):
        initializedEnsembles = []
        potentialEnsembles = sorted(potentialEnsembles)
        for ens in potentialEnsembles:
            if ens.materialize(components, initializedEnsembles):
                initializedEnsembles.append(ens)
                ens.actuate()
