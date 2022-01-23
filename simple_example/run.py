# This is to disable logging and use of GPU in TensorFLow
import os
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")  # Report only TF errors by default
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Disable GPU in TF. The models are small, so it is actually faster to use the CPU.
import tensorflow as tf
# Fix random seed
tf.random.set_seed(42)

from drone import Drone
from package_ensemble import PackageEnsemble

from ml_deeco.simulation import Point, run_experiment
from ml_deeco.utils import setVerboseLevel, Log

setVerboseLevel(2)


drone = Drone(Point(0, 0))
packageEnsemble = PackageEnsemble(Point(9, 0))

log: Log = None  # type: ignore


def prepareSimulation(iteration, simulation):
    global drone
    drone = Drone(Point(0, 0))
    if iteration > 0:
        drone.useEstimate = True

    components = [drone]
    ensembles = [packageEnsemble]
    return components, ensembles


def logStepData(components, materializedEnsembles, step):
    log.register([f"{drone.location.x:.0f}", f"{drone.battery:.2f}", f"{drone.futureBatteryEstimate():.2f}", drone.state])


def prepareIteration(iteration):
    global log
    log = Log(["location", "battery", "future_battery", "state"])


def iterationCallback(iteration):
    log.export(f"results/log_{iteration + 1}.csv")


run_experiment(
    iterations=2,
    simulations=1,
    steps=80,
    prepareSimulation=prepareSimulation,
    prepareIteration=prepareIteration,
    iterationCallback=iterationCallback,
    stepCallback=logStepData,
)
