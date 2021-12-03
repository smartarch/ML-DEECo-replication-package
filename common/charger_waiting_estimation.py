"""
Charger waiting time estimation
"""


def getChargerWaitingTimeEstimation(world, baseline, outputFolder):
    # TODO(MT): the imports need to be here in order to prevent circular references, we should probably redo this in a better way by creating a class for the ChargerWaitingTimeEstimation
    import math
    from common.components import DroneState
    from common.estimator import BaselineEstimation, FloatFeature, IntEnumFeature, NeuralNetworkTimeEstimation

    estimationInputs = {
        'drone_battery': FloatFeature(0, 1),
        'drone_state': IntEnumFeature(DroneState),
        'charger_distance': FloatFeature(0, math.sqrt(world.mapWidth ** 2 + world.mapHeight ** 2)),
        'queue_length': FloatFeature(0, len(world.drones) / world.chargerCapacity),  # number of drones in the waiting queue divided by the number of drones which can be charged simultaneously
        'charging_drones': FloatFeature(0, world.chargerCapacity),  # number of drones currently being charged
    }

    if baseline:
        return BaselineEstimation(estimationInputs)
    else:
        return NeuralNetworkTimeEstimation(estimationInputs, outputFolder)


def generateFeatures(charger, drone):
    return {
        'drone_battery': drone.battery,
        'drone_state': int(drone.state),
        'charger_distance': charger.location.distance(drone.location),
        'queue_length': len(charger.chargingQueue) / charger.chargerCapacity,
        'charging_drones': len(charger.chargingDrones),
    }
