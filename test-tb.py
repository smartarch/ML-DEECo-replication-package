""" 
    A play ground for testing the developed classes and methods.
"""

from source.base import Point, Charger, Drone, Bird, Field, DroneState
from source.tasks import ChargerAssignment

charger_1 = Charger(
    location=Point(0.1, 0.1)
)
charger_2 = Charger(
    location=Point(0.4, 0.7)
)

charger_3 = Charger(
    location=Point(0.5, 0.3)
)

components = [
    charger_1,
    charger_2,
    charger_3,
    Drone(
        location=Point(0.2, 0.1)
    ),
    Drone(
        location=Point(0.3, 0.1)
    )
]

ca1 = ChargerAssignment(charger_1)
ca2 = ChargerAssignment(charger_2)
ca3 = ChargerAssignment(charger_3)

potentialEnsembles = [ca1, ca2, ca3]
potentialEnsembles = sorted(potentialEnsembles, key=lambda x: x.priority())

instantiatedEnsembles = []
for ens in potentialEnsembles:
    if ens.materialize(components, instantiatedEnsembles):
        instantiatedEnsembles.append(ens)
        ens.actuate()
