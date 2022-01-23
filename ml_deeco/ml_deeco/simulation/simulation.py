from datetime import datetime

from ml_deeco.utils import verbosePrint


class SimulationGlobals:

    def __init__(self):
        if 'SIMULATION_GLOBALS' in locals():
            raise RuntimeError("Do not create a new instance of the SimulationGlobals. Use the SIMULATION_GLOBALS global variable instead.")
        self.estimators = []
        self.currentTimeStep = 0

    def initEstimators(self):
        """Initialize the estimators. This has to be called after the components and ensembles are imported."""
        for est in self.estimators:
            est.init()


SIMULATION_GLOBALS = SimulationGlobals()


def materialize_ensembles(components, ensembles):
    initializedEnsembles = []

    potentialEnsembles = sorted(ensembles)
    for ens in potentialEnsembles:
        if ens.materialize(components, initializedEnsembles):
            initializedEnsembles.append(ens)
            ens.actuate()
    for ens in initializedEnsembles:
        ens.collectEstimatesData(components)

    return initializedEnsembles


def actuate_components(components):
    for component in components:
        component.actuate()
        verbosePrint(f"{component}", 4)
    for component in components:
        component.collectEstimatesData()


def run_simulation(components, ensembles, steps, stepCallback=None):

    for step in range(steps):

        verbosePrint(f"Step {step + 1}:", 3)
        SIMULATION_GLOBALS.currentTimeStep = step

        materializedEnsembles = materialize_ensembles(components, ensembles)
        actuate_components(components)

        if stepCallback:
            stepCallback(components, materializedEnsembles, step)


def run_experiment(iterations, simulations, steps, prepareSimulation, prepareIteration=None,
                   iterationCallback=None, simulationCallback=None, stepCallback=None):

    SIMULATION_GLOBALS.initEstimators()

    for iteration in range(iterations):
        verbosePrint(f"Iteration {iteration + 1} started at {datetime.now()}:", 1)
        if prepareIteration:
            prepareIteration(iteration)

        for simulation in range(simulations):
            verbosePrint(f"Simulation {simulation + 1} started at {datetime.now()}:", 2)

            components, ensembles = prepareSimulation(iteration, simulation)

            run_simulation(components, ensembles, steps, stepCallback)

            if simulationCallback:
                simulationCallback(components, ensembles, iteration, simulation)

        for estimator in SIMULATION_GLOBALS.estimators:
            estimator.endIteration()

        if iterationCallback:
            iterationCallback(iteration)
