from simulation.drone_state import DroneState
from simulation.world import WORLD, ENVIRONMENT
from utils.verbose import verbosePrint
from utils.visualizers import Visualizer


# TODO: as the world is global, this might be only a function (or multiple functions) instead of a class
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

    def run(self, filename, args):

        components = []

        components.extend(self.world.drones)
        components.extend(self.world.birds)
        components.extend(self.world.chargers)

        from ensembles.field_protection import getEnsembles as fieldProtectionEnsembles
        from ensembles.drone_charging import getEnsembles as droneChargingEnsembles
        potentialEnsembles = fieldProtectionEnsembles(self.world) + droneChargingEnsembles(self.world)

        WORLD.initEstimations()

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

            # Components
            for component in components:
                component.actuate()
                verbosePrint(f"{component}", 4)

            # Collect statistics
            for chargerIndex in range(len(self.world.chargers)):
                charger = self.world.chargers[chargerIndex]
                self.world.chargerLogs[chargerIndex].register([
                    # sum([drone.battery for drone in charger.potentialDrones])/potentialDrones,
                    len(charger.chargingDrones),
                    len(charger.acceptedDrones),
                    len(charger.potentialDrones),
                ])

            if self.visualize:
                visualizer.drawComponents(i + 1)

        if self.visualize:
            verbosePrint(f"Saving animation...", 2)
            visualizer.createAnimation(f"{self.folder}/animations/{filename}.gif")
            verbosePrint(f"Animation saved.", 2)

        self.world.chargerLog.export(f"{self.folder}/charger_logs/{filename}.csv")
        totalLog = self.collectStatistics()

        return totalLog, self.world.chargerLogs

    def actuateEnsembles(self, potentialEnsembles, components):
        initializedEnsembles = []
        potentialEnsembles = sorted(potentialEnsembles)
        for ens in potentialEnsembles:
            if ens.materialize(components, initializedEnsembles):
                initializedEnsembles.append(ens)
                ens.actuate()
