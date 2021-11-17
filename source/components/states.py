from enum import Enum
class BirdState(Enum):
    """
        An enumerate property for the birds.
        IDLE: a default state for birds, when they are out of fields.
        ATTACKING: a state where a bird has a field in mind, and attacking it.
        FLEEING: a state where a bird is running away from drones
    """

    IDLE = 0
    MOVING = 1
    OBSERVING = 2
    EATING = 3
    FLEEING = 4




class DroneState(Enum):
    """
        An enumerate property for the drones.
        IDLE: a default state for drones.
        PROTECTING: when the drones are protecting the zones.
        MOVING_TO_CHARGING: when the drones are moving/queuing for a charger.
        CHARGIN: when the drones are being chareged.
        TERMINATED: when the drone's battery is below 0 and they do not operate anymore.
    """

    IDLE = 0
    PROTECTING = 1
    MOVING_TO_FIELD = 2
    MOVING_TO_CHARGER = 3
    CHARGING = 4
    TERMINATED = 5