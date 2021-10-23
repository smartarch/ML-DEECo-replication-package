""" 
    A play ground for testing the developed classes and methods.
"""

from source.base import Point, Charger, Drone, Bird, Field, DroneState
from source.tasks import ChargerAssignment

charger_1 = Charger(
    location=Point(0.1, 0.1)
)

components = [
    charger_1,
    Drone(
        location=Point(0.2, 0.1)
    ),
    Drone(
        location=Point(0.3, 0.1)
    )
]

ca = ChargerAssignment(charger_1)
ca.materialize(components, [])
print(ca.drone)



