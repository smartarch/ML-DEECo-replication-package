"""
Charger waiting time estimation
"""


def getChargerWaitingTimeEstimation(world, baseline):
    # TODO(MT): the imports need to be here in order to prevent circular references, we should probably redo this in a better way by creating a class for the ChargerWaitingTimeEstimation
    import math
    from common.components import DroneState
    from common.estimator import BaselineEstimation, FloatFeature, IntEnumFeature, NeuralNetworkTimeEstimation

    estimationInputs = {
        'drone_battery': FloatFeature(0, 1),
        'drone_state': IntEnumFeature(DroneState),
        'charger_distance': FloatFeature(0, math.sqrt(world.mapWidth ** 2 + world.mapHeight ** 2)),
        # TODO(MT): more features
    }

    if baseline:
        return BaselineEstimation(estimationInputs)
    else:
        return NeuralNetworkTimeEstimation(estimationInputs)


def generateFeatures(charger, drone):
    return {
        'drone_battery': drone.battery,
        'drone_state': int(drone.state),
        'charger_distance': charger.location.distance(drone.location),
    }
