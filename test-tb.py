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
ca2 = ChargerAssignment(charger_2)
ca3 = ChargerAssignment(charger_3)

potentialEnsembles = [ca, ca2, c3]
portentialEnsembles = sorted(potentialEnsembles, key=lambda x: x.priority())

instantiatedEnsembles = []
for ens in potentialEnsembles:
    if ca.materialize(components, instantiatedEnsembles):
        instantiatedEnsembles.append(ens)
        ens.actuate()
