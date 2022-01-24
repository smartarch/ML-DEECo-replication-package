# This is to disable logging and use of GPU in TensorFLow
import os
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")  # Report only TF errors by default
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Disable GPU in TF. The models are small, so it is actually faster to use the CPU.
import tensorflow as tf
# Fix random seed
tf.random.set_seed(42)

from matplotlib import pyplot as plt

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
    log.register([drone.location.x, drone.battery, drone.futureBatteryEstimate(), drone.state])


def prepareIteration(iteration):
    global log
    log = Log({
        "location": ".0f",
        "battery": ".2f",
        "future_battery": ".2f",
        "state": None
    })


def drawPlot(iteration):
    location = log.getColumn("location")
    battery = log.getColumn("battery")
    futureBattery = log.getColumn("future_battery")

    fig, ax1 = plt.subplots()
    plt.title(f"Iteration: {iteration}")
    ax1.set_xlabel('Step')

    ax1.set_ylabel('Battery')
    ax1.plot(battery, color='tab:green', label='Battery')
    ax1.plot(futureBattery, color='tab:blue', label='Future battery')

    ax2 = ax1.twinx()
    ax2.set_ylabel('Location')
    ax2.plot(location, color='tab:red', label='Location')

    fig.tight_layout()
    plt.show()


def iterationCallback(iteration):
    log.export(f"results/log_{iteration + 1}.csv")
    drawPlot(iteration + 1)


run_experiment(
    iterations=2,
    simulations=1,
    steps=80,
    prepareSimulation=prepareSimulation,
    prepareIteration=prepareIteration,
    iterationCallback=iterationCallback,
    stepCallback=logStepData,
)
