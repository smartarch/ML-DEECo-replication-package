from simulation.drone_state import DroneState
from simulation.world import WORLD, ENVIRONMENT
from utils.verbose import verbosePrint
from utils.visualizers import Visualizer
from utils.serialization import Log


class Simulation:

    def __init__(self, folder, visualize):
        self.visualize = visualize
        self.folder = folder
        self.MAXDRONES = ENVIRONMENT.droneCount
        self.MAXDAMAGE = ENVIRONMENT.birdCount * ENVIRONMENT.maxSteps
        self.MAXENERGY = ENVIRONMENT.chargerCount * ENVIRONMENT.chargerCapacity * ENVIRONMENT.chargingRate * ENVIRONMENT.maxSteps



    def collectStatistics(self,train,iteration):
        return [
            train+1,
            iteration+1,
            len([drone for drone in WORLD.drones if drone.state != DroneState.TERMINATED]),
            sum([bird.ate for bird in WORLD.birds]),
            sum([charger.energyConsumed for charger in WORLD.chargers])
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
            len([drone for drone in WORLD.drones if drone.state != DroneState.TERMINATED]),
            len([drone for drone in WORLD.drones if drone.state != DroneState.TERMINATED])/self.MAXDRONES,
            sum([bird.ate for bird in WORLD.birds])-previousRates['Damage'],
            sum([bird.ate for bird in WORLD.birds]),
            sum([charger.energyConsumed for charger in WORLD.chargers])-previousRates['Energy'],
            sum([charger.energyConsumed for charger in WORLD.chargers])
        ]
    def run(self, filename,train,iteration, args):

        components = []

        components.extend(WORLD.drones)
        components.extend(WORLD.birds)
        components.extend(WORLD.chargers)

        from ensembles.field_protection import getEnsembles as fieldProtectionEnsembles
        from ensembles.drone_charging import getEnsembles as droneChargingEnsembles
        potentialEnsembles = fieldProtectionEnsembles(WORLD) + droneChargingEnsembles(WORLD)

        WORLD.initEstimators()

        if self.visualize:
            visualizer = Visualizer(WORLD)
            visualizer.drawFields()

        for i in range(ENVIRONMENT.maxSteps):
            verbosePrint(f"Step {i + 1}:", 3)
            WORLD.currentTimeStep = i

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
            for chargerIndex in range(len(WORLD.chargers)):
                charger = WORLD.chargers[chargerIndex]
                accepted = set(charger.acceptedDrones)
                waiting = set(charger.waitingDrones)
                potential = set(charger.potentialDrones)
                WORLD.chargerLogs[chargerIndex].register([
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
            visualizer.createAnimation(f"{self.folder}/animations/{filename}_{train+1}_{iteration+1}.gif")
            verbosePrint(f"Animation saved.", 3)

        WORLD.chargerLog.export(f"{self.folder}/charger_logs/{filename}_{train+1}_{iteration+1}.csv")
        totalLog = self.collectStatistics(train,iteration)

        return totalLog, WORLD.chargerLogs


    def quickrun(self, filename,train,iteration, args):
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

        components.extend(WORLD.drones)

        components.extend(WORLD.birds)
        components.extend(WORLD.chargers)

        from ensembles.field_protection import getEnsembles as fieldProtectionEnsembles
        from ensembles.drone_charging import getEnsembles as droneChargingEnsembles
        potentialEnsembles = fieldProtectionEnsembles(WORLD) + droneChargingEnsembles(WORLD)

        WORLD.initEstimators()

        if self.visualize:
            visualizer = Visualizer(WORLD)
            visualizer.drawFields()
        previousRates = None
        for i in range(ENVIRONMENT.maxSteps):
            verbosePrint(f"Step {i + 1}:", 3)
            WORLD.currentTimeStep = i

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
            visualizer.createAnimation(f"{self.folder}/animations/{filename}_{train+1}_{iteration+1}.gif")
            verbosePrint(f"Animation saved.", 3)

        WORLD.chargerLog.export(f"{self.folder}/charger_logs/{filename}_{train+1}_{iteration+1}.csv") 
        
        WORLD.currentTimeStep = ENVIRONMENT.maxSteps
        log.register(self.collectRates(previousRates))
        log.export(f"{self.folder}/{filename}_{train+1}_{iteration+1}.csv")
        return self.collectStatistics(train,iteration), WORLD.chargerLogs

    def actuateEnsembles(self, potentialEnsembles, components):
        initializedEnsembles = []
        potentialEnsembles = sorted(potentialEnsembles)
        for ens in potentialEnsembles:
            if ens.materialize(components, initializedEnsembles):
                initializedEnsembles.append(ens)
                ens.actuate()
