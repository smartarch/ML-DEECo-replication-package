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

    for i in range(steps):

        verbosePrint(f"Step {i + 1}:", 3)
        SIMULATION_GLOBALS.currentTimeStep = i

        materializedEnsembles = materialize_ensembles(components, ensembles)
        actuate_components(components)

        if stepCallback:
            stepCallback(components, materializedEnsembles, i)
