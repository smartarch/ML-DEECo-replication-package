""" 
    A play ground for testing the developed classes and methods.
"""

from source.serializer import ComponentSerializer as CS
from source.base import Drone , Point
from source.simulation import World

k = [
    Drone(Point(0.1,.7)),
    Drone(Point(0.3,.4)),
    Drone(Point(0.2,.5)),
    Drone(Point(0.4,.6)),
    Drone(Point(0.1,.2)),
]

tk = CS(k)
tk.to_yaml("test1.yaml", True)


fk = CS.from_yaml("test1.yaml")